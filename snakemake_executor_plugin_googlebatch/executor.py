import os
import uuid

from typing import List, Generator
from snakemake_interface_executor_plugins.executors.base import SubmittedJobInfo
from snakemake_interface_executor_plugins.executors.remote import RemoteExecutor
from snakemake_interface_executor_plugins.workflow import WorkflowExecutorInterface
from snakemake_interface_executor_plugins.logging import LoggerExecutorInterface
from snakemake_interface_executor_plugins.jobs import (
    JobExecutorInterface,
)
from snakemake.common import get_container_image
from snakemake_interface_common.exceptions import WorkflowError  # noqa
import snakemake_executor_plugin_googlebatch.utils as utils
import snakemake_executor_plugin_googlebatch.command as cmdutil

from google.cloud import batch_v1


class GoogleBatchExecutor(RemoteExecutor):
    def __init__(
        self,
        workflow: WorkflowExecutorInterface,
        logger: LoggerExecutorInterface,
    ):
        super().__init__(workflow, logger)

        # Attach variables for easy access
        self.workdir = os.path.realpath(os.path.dirname(self.workflow.persistence.path))

        # There is an async client but I'm not sure we'd get much benefit
        self.batch = batch_v1.BatchServiceClient()

    def get_param(self, job, param):
        """
		Simple courtesy function to get a job resource and fall back to defaults.
		
		1. First preference goes to googlebatch_ directive in step
		2. Second preference goes to command line flag
		3. Third preference falls back to default
		""" 
        return job.resources.get(f"googlebatch_{param}") or getattr(self.executor_settings, param, None)


    def get_task_resources(self, job):
        """
        Get task compute resources.

        CPU Milli are milliseconds per cpu-second. 
        These are the requirement % of a single CPUs.
        """
        resources = batch_v1.ComputeResource()
        memory = self.get_param(job, "memory") 
        cpu_milli = self.get_param(job, "cpu_milli") 
        resources.cpu_milli = cpu_milli
        resources.memory_mib = memory
        return resources


    def get_labels(self, job):
        """
        Derive default labels for the job (and add custom)
        """
        labels = {"snakemake-job": job.name}
        for contender in self.get_param(job, "labels").split(','):
            if not contender:
                continue
            if "=" not in contender:
                self.logger.warning(f'Label group {contender} is missing an "="')
                continue
            key, value = contender.split('=', 1)
            labels[key] = value
        return labels


    def add_storage(self, job, task):
        """
        Add storage for a task, which requires a bucket and mount path.
        """
        bucket = self.get_param(job, "bucket") 
        if not bucket:
            return

        gcs_bucket = batch_v1.GCS()
        gcs_bucket.remote_path = bucket
        gcs_volume = batch_v1.Volume()
        gcs_volume.gcs = gcs_bucket
        gcs_volume.mount_path = self.get_param(job, "mount_path")
        task.volumes = [gcs_volume]


    def generate_jobid(self, job):
        """
        Generate a random jobid
        """
        uid = str(uuid.uuid4())
        return job.name.replace('_', '-') + "-" + uid[0:6]

    def validate(self, job):
        """
        Ensure the choices of arguments make sense.
        """
        container = self.get_container(job)
        family = self.get_param(job, "image_family") 

        # We can't take a custom container if batch-cos is not set
        # We only give a warning here in case it's a one-off setting
        if family != "batch-cos" and container:
            self.logger.warning(f"Job {job} has container without image_family batch-cos.")

    def get_container(self, job):
        """
        Get container intended for a job
        """
        return job.resources.get("container") or self.executor_settings.container

    def derive_setup_command(self, job):
        """
        Derive a setup command for a job.

        This largely depends on the image family selected to either install
        snakemake or run a container on batch-cos.
        """
        family = self.get_param(job, "image_family") 

        # If batch-cos is the image family we will use a container
        container = self.get_container(job) or get_container_image()

        # We will write the Snakefile to the worker (this is the contents)
        snakefile = self.read_snakefile()

        # Derive the command. E.g., COS will likely run the snakemake container
        # And installs depend on the base operating system we find
        command = cmdutil.derive_setup_command(container, family, snakefile)        
        self.logger.info("\n🌟️ Setup Command:")
        print(command)
        return command

    def derive_command(self, job):
        """
        Derive a command for a job.

        This largely depends on the image family selected to either install
        snakemake or run a container on batch-cos.
        """
        family = self.get_param(job, "image_family") 
        command = self.format_job_exec(job)
        command = cmdutil.derive_command(command, family)
        self.logger.info("\n🐍️ Snakemake Command:")
        print(command)
        return command

    def run_job(self, job: JobExecutorInterface):
        """
        Run the Google Batch job.

        This involves creating one or more runnables that are packaged in
        a task, and the task is put into a group that is associated with a job.
        """
        logfile = job.logfile_suggestion(os.path.join(".snakemake", "googlebatch_logs"))
        os.makedirs(os.path.dirname(logfile), exist_ok=True)

        # This will create one simple runnable for a task
        task = batch_v1.TaskSpec()
        task.max_retry_count = self.get_param(job, "retry_count") 
        task.max_run_duration = self.get_param(job, "max_run_duration") 

        # A single runnable to execute snakemake
        runnable = batch_v1.Runnable()
        runnable.script = batch_v1.Runnable.Script()
        runnable.script.text = self.derive_command(job)

        # Snakemake setup must finish before snakemake is run
        setup = batch_v1.Runnable()
        setup.script = batch_v1.Runnable.Script()
        setup.script.text = self.derive_setup_command(job)

        # This will ensure all nodes finish first
        barrier = batch_v1.Runnable()
        barrier.barrier = batch_v1.Runnable.Barrier()
        barrier.barrier.name = "wait-for-setup"
        task.runnables = [setup, barrier, runnable] 

        # Are we adding storage?
        self.add_storage(job, task)

        # We can specify what resources are requested by each task.
        task.compute_resource = self.get_task_resources(job)

        # Tasks are grouped inside a job using TaskGroups.
        # Currently, it's possible to have only one task group.
        group = batch_v1.TaskGroup()
        group.task_count_per_node = self.get_param(job, "work_tasks_per_node") 
        group.task_count = self.get_param(job, "work_tasks") 
        group.task_spec = task

        # Right now I don't see a need to not allow this
        group.require_hosts_file = True
        group.permissive_ssh = True

        # This includes instances (machine type) boot disk and policy
        policy = self.get_allocation_policy(job)

        batchjob = batch_v1.Job()
        batchjob.task_groups = [group]
        batchjob.allocation_policy = policy
        batchjob.labels = self.get_labels(job)

        # We use Cloud Logging as it's an out of the box available option
        batchjob.logs_policy = batch_v1.LogsPolicy()
        batchjob.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

        create_request = batch_v1.CreateJobRequest()
        create_request.job = batchjob
        create_request.job_id = self.generate_jobid(job)

        # The job's parent is the region in which the job will run
        create_request.parent = self.project_parent(job)
        createdjob = self.batch.create_job(create_request)

        # Save aux metadata
        # Last seen will hold the timestamp of last recorded status
        aux = {"batch_job": createdjob, "logfile": logfile, "last_seen": None}

        # Record job info - the name is what we use to get a status later
        self.report_job_submission(SubmittedJobInfo(job, external_jobid=createdjob.name, aux=aux))


# TODO need to think about how a more complex startup script will work
# This would go after the variable specification
    # Prepare the script templates
#    run_template = jinja2.Template(run_script)
#    runscript = run_template.render(
#        {
#            "tasks": tasks,
#            "tasks_per_node": tasks_per_node,
#            "outdir": outdir,
#        }
#    )

#    setup_template = jinja2.Template(setup_script)
#    script = setup_template.render({"outdir": outdir})

    # Write over same file here, yes bad practice and lazy
#    template_and_write("setup.sh", script, bucket_name, "hello-world-mpi/setup.sh")
#    template_and_write("run.sh", runscript, bucket_name, "hello-world-mpi/run.sh")
#    upload_to_bucket("hello-world-mpi/Makefile", "Makefile", bucket_name)

# TODO need to think about how we want to separate some setup section (and barrier)

#    # Define what will be done as part of the job.
#    task = batch_v1.TaskSpec()


    def project_parent(self, job):
        """
        The job's parent is the region in which the job will run.
        """
        project_id = self.get_param(job, "project")
        region = self.get_param(job, "region")
        return f"projects/{project_id}/locations/{region}"


    def get_allocation_policy(self, job):
        """
        Get allocation policy for a job. This includes:

        An allocation policy.
        A boot disk attached to the allocation policy.
        Instances with a particular machine / image family.
        """
        machine_type = self.get_param(job, "machine_type") 
        family = self.get_param(job, "image_family") 
        project = self.get_param(job, "image_project") 

        # Disks is how we specify the image we want (we need centos to get MPI working)        
        # This could also be batch-centos, batch-debian, batch-cos
        # but MPI won't work on all of those
        boot_disk = batch_v1.AllocationPolicy.Disk()
        boot_disk.image = f"projects/{project}/global/images/family/{family}"

        # Policies are used to define on what kind of virtual machines the tasks will run on.
        # https://github.com/googleapis/python-batch/blob/main/google/cloud/batch_v1/types/job.py#L383
        allocation_policy = batch_v1.AllocationPolicy()
        policy = batch_v1.AllocationPolicy.InstancePolicy()
        policy.machine_type = machine_type
        policy.boot_disk = boot_disk

        instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
        instances.policy = policy
        allocation_policy.instances = [instances]
        return allocation_policy

    def read_snakefile(self):
        """
        Get the content of the Snakefile to write to the worker.
        
        This might need to be improved to support storage, etc.
        """
        assert os.path.exists(self.workflow.main_snakefile)
        return utils.read_file(self.workflow.main_snakefile)

    def get_snakefile(self):
        """
        Use a Snakefile in the present working directory since we write it.
        """
        assert os.path.exists(self.workflow.main_snakefile)
        return "Snakefile"


    async def check_active_jobs(
        self, active_jobs: List[SubmittedJobInfo]
    ) -> Generator[SubmittedJobInfo, None, None]:
        """
        Check the status of active jobs.
        """
        # Loop through active jobs and act on status
        for j in active_jobs:
            jobid = j.external_jobid
            request = batch_v1.GetJobRequest(name=jobid)
            response = self.batch.get_job(request=request)

            # Aux logs are consistently here
            aux_logs = [j.aux["logfile"]]
            last_seen = j.aux["last_seen"]

            self.logger.info(f"Job {jobid} has state {response.status.state.name}")
            for event in response.status.status_events:
                if not last_seen or event.event_time.nanosecond > last_seen:
                    self.logger.info(f"{event.type_}: {event.description}")
                    last_seen = event.event_time.nanosecond

            # Update last seen for next time (TODO not sure this is sticking)
            j.aux['last_seen'] = last_seen

            # Possible statuses:
            # RUNNING
            # SCHEDULED
            # QUEUED
            # STATE_UNSPECIFIED
            # SUCCEEDED
            # FAILED
            # DELETION_IN_PROGRESS
            if response.status.state.name == "FAILED":
                msg = f"Google Batch job '{j.external_jobid}' failed. "
                self.report_job_error(j, msg=msg, aux_logs=aux_logs)

            elif response.status.state.name == "SUCCEEDED":
                self.report_job_success(j)

            # Otherwise, we are queued / scheduled / running, etc.
            else:
                yield j


    def cancel_jobs(self, active_jobs: List[SubmittedJobInfo]):
        """
        cancel all active jobs. This method is called when snakemake is interrupted.
        """
        for job in active_jobs:
            jobid = job.external_jobid
            reason = f"User requested cancel for {jobid}"
            request = batch_v1.DeleteJobRequest(name=jobid, reason=reason)
            operation = self.batch.delete_job(request=request)
            self.logger.info(f"Waiting for job {jobid} to cancel...")
            response = operation.result()
            self.logger.info(response)
        # self.shutdown()
