import os
import time
import uuid

from typing import List
from snakemake_interface_common.exceptions import WorkflowError
from snakemake_interface_executor_plugins.executors.base import SubmittedJobInfo
from snakemake_interface_executor_plugins.executors.remote import RemoteExecutor
from snakemake_interface_executor_plugins.jobs import (
    JobExecutorInterface,
)
import snakemake_executor_plugin_googlebatch.utils as utils
import snakemake_executor_plugin_googlebatch.command as cmdutil

from google.api_core.exceptions import DeadlineExceeded, ResourceExhausted
from google.cloud import batch_v1, logging


class GoogleBatchExecutor(RemoteExecutor):
    def __post_init__(self):
        # Attach variables for easy access
        self.workdir = os.path.realpath(os.path.dirname(self.workflow.persistence.path))

        # There is an async client but I'm not sure we'd get much benefit
        try:
            self.batch = batch_v1.BatchServiceClient()
        except Exception as e:
            raise WorkflowError("Unable to connect to Google Batch.", e)

    def get_param(self, job, param):
        """
        Simple courtesy function to get a job resource and fall back to defaults.

        1. First preference goes to googlebatch_ directive in step
        2. Second preference goes to command line flag
        3. Third preference falls back to default
        """
        return job.resources.get(f"googlebatch_{param}") or getattr(
            self.executor_settings, param, None
        )

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
        labels = {"snakemake-job": self.fix_job_name(job.name)}
        for contender in self.get_param(job, "labels").split(","):
            if not contender:
                continue
            if "=" not in contender:
                self.logger.warning(f'Label group {contender} is missing an "="')
                continue
            key, value = contender.split("=", 1)
            labels[key] = value
        return labels

    def get_envvar_declarations(self):
        """
        This is just added as a workaround while there is a bug with real.py
        """
        return {}

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
        return self.fix_job_name(job.name) + "-" + uid[0:6]

    def get_container(self, job, entrypoint=None, commands=None):
        """
        Get a container, if batch-cos is defined.
        """
        family = self.get_param(job, "image_family")
        if "batch-cos" not in family:
            return

        # Default entrypoint assumes the setup wrote our command here
        if entrypoint is None:
            entrypoint = "/bin/bash"
        if commands is None:
            commands = ["/tmp/workdir/entrypoint.sh"]

        # We use the default snakemake image or the container, but also
        # honor a googlebatch_container in case it is distinct
        image = self.workflow.remote_execution_settings.container_image
        image = self.get_param(job, "container") or image
        container = batch_v1.Runnable.Container()
        container.image_uri = image

        # This is written by writer.setup() for COS
        container.entrypoint = entrypoint
        container.commands = commands

        # This will ensure the Snakefile is in the PWD of the COS container
        container.volumes = ["/tmp/workdir:/tmp/workdir"]
        container.options = (
            "--network host --workdir /tmp/workdir -e PYTHONUNBUFFERED=1"
        )

        username = self.get_param(job, "docker_username")
        password = self.get_param(job, "docker_password")

        # Both are required
        if (username and not password) or (password and not username):
            raise WorkflowError(
                "docker username and password are required if one is provided"
            )

        if username and password:
            container.username = username
            container.password = password

        # Not sure if we want to add this
        # https://github.com/googleapis/googleapis/blob/master/google/cloud/batch/v1/task.proto#L230-L234
        # enable_image_streaming true
        return container

    def is_preemptible(self, job):
        """
        Determine if a job is preemptible.

        The logic for determining if the set is valid should belong upstream.
        """
        is_p = self.workflow.remote_execution_settings.preemptible_rules.is_preemptible
        if job.is_group():
            preemptible = all(is_p(rule) for rule in job.rules)
        else:
            preemptible = is_p(job.rule.name)
        return preemptible

    def get_command_writer(self, job):
        """
        Get a command writer for a job.
        """
        family = self.get_param(job, "image_family")
        command = self.format_job_exec(job)
        snakefile = self.read_snakefile()

        # Any custom snippets
        snippets = self.get_param(job, "snippets")

        snakefile_path = "./Snakefile"
        if "batch-cos" in family:
            snakefile_path = "/tmp/workdir/Snakefile"
        return cmdutil.get_writer(family)(
            command=command,
            snakefile=snakefile,
            snippets=snippets,
            snakefile_path=snakefile_path,
            settings=self.workflow.executor_settings,
            resources=job.resources,
        )

    def fix_job_name(self, name):
        """
        Replace illegal symbols and fix the job name length to adhere to
        the Google Batch API job ID and label naming restrictions
        """
        return name.replace("_", "-").replace(".", "")[:50]

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

        # The command writer prepares the final command, snippets, etc.
        writer = self.get_command_writer(job)

        # Setup command
        setup_command = writer.setup()
        self.logger.info("\n🌟️ Setup Command:")
        print(setup_command)

        # Add environment variables to the task
        envars = self.workflow.spawned_job_args_factory.envvars()

        # A single runnable to execute snakemake
        runnable = batch_v1.Runnable()

        # If we have a container, add it - the script isn't used
        container = self.get_container(job)
        if container is not None:
            runnable.container = container
            snakefile_text = writer.write_snakefile()
        else:
            # Run command (not used for COS)
            run_command = writer.run()
            self.logger.info("\n🐍️ Snakemake Command:")
            print(run_command)

            runnable.script = batch_v1.Runnable.Script()
            runnable.script.text = run_command
            snakefile_text = writer.write_snakefile()

        # Runnable to write Snakefile on the host
        snakefile_step = batch_v1.Runnable()
        snakefile_step.script = batch_v1.Runnable.Script()
        snakefile_step.script.text = snakefile_text

        # Note that secret variables seem to require some
        # extra secret API enabled
        runnable.environment.variables = envars

        # Snakemake setup must finish before snakemake is run
        setup = batch_v1.Runnable()
        setup.script = batch_v1.Runnable.Script()
        setup.script.text = setup_command

        # Placement policy
        # https://cloud.google.com/python/docs/reference/batch/latest/google.cloud.batch_v1.types.AllocationPolicy.PlacementPolicy

        # This will ensure all nodes finish first
        barrier = batch_v1.Runnable()
        barrier.barrier = batch_v1.Runnable.Barrier()
        barrier.barrier.name = "wait-for-setup"
        task.runnables = [setup, snakefile_step, barrier, runnable]

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
        # Also preemtion
        policy = self.get_allocation_policy(job)

        # If we have preemption for the job and retry, update task retries with it
        retries = self.workflow.remote_execution_settings.preemptible_retries
        if self.is_preemptible(job) and retries:
            self.logger.debug(f"Updating preemptible retries to {retries}")
            task.max_retry_count = retries

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
        print(createdjob)

        # Save aux metadata
        # Last seen will hold the timestamp of last recorded status
        aux = {"batch_job": createdjob, "logfile": logfile, "last_seen": None}

        # Record job info - the name is what we use to get a status later
        self.report_job_submission(
            SubmittedJobInfo(job, external_jobid=createdjob.name, aux=aux)
        )

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

        # Policies are used to define on what kind of VM the tasks will run on.
        allocation_policy = batch_v1.AllocationPolicy()
        policy = batch_v1.AllocationPolicy.InstancePolicy()
        policy.machine_type = machine_type
        policy.boot_disk = boot_disk

        # Do we want preemptible?
        # https://github.com/googleapis/googleapis/blob/master/google/cloud/batch/v1/job.proto#L479 and  # noqa
        # https://github.com/googleapis/google-cloud-python/blob/main/packages/google-cloud-batch/google/cloud/batch_v1/types/job.py#L672  # noqa
        if self.is_preemptible(job):
            policy.provisioning_model = 3

        instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()

        # Are we requesting GPU / accelerators?
        accelerators = self.get_accelerators(job)
        if accelerators:
            instances.install_gpu_drivers = True
            policy.accelerators = accelerators

        # Customize boot disk
        boot_disk = self.get_boot_disk(job)
        if boot_disk is not None:
            policy.boot_disk = boot_disk

        instances.policy = policy
        allocation_policy.instances = [instances]

        # Add custom network interfaces
        network_policy = self.get_network_policy(job)
        if network_policy is not None:
            allocation_policy.network = network_policy
            # Add custom compute service account
        service_account = self.get_service_account(job)

        if service_account is not None:
            allocation_policy.service_account = service_account

        return allocation_policy

    def get_network_policy(self, job):
        """
        Given a job request, get the network policy
        """
        network = self.get_param(job, "network")
        subnetwork = self.get_param(job, "subnetwork")
        if all(x is None for x in [network, subnetwork]):
            return

        policy = batch_v1.AllocationPolicy.NetworkPolicy()
        interface = batch_v1.AllocationPolicy.NetworkInterface()
        if network is not None:
            interface.network = network
        if subnetwork is not None:
            interface.subnetwork = subnetwork
        policy.network_interfaces = [interface]
        return policy

    def get_service_account(self, job: JobExecutorInterface) -> batch_v1.ServiceAccount:
        """
        Givena job request, get the service account
        """
        service_account_email = self.get_param(job, "service_account")
        service_account = batch_v1.ServiceAccount()
        if service_account_email is not None:
            service_account.email = service_account_email
        return service_account

    def get_boot_disk(self, job):
        """
        Given a job request, add a customized boot disk.
        """
        # Reference disk, boot disk type, and size
        image = self.get_param(job, "boot_disk_image")
        size = self.get_param(job, "boot_disk_gb")
        typ = self.get_param(job, "boot_disk_type")

        # Cut out early if no customization
        if all(x is None for x in [image, size, typ]):
            return

        boot_disk = batch_v1.AllocationPolicy.Disk()
        if image is not None:
            boot_disk.image = image
        if size is not None:
            boot_disk.size_gb = size
        if typ is not None:
            boot_disk.type_ = typ
        return boot_disk

    def get_accelerators(self, job):
        """
        Given a job request, add accelerators (count and type) to it.
        """
        gpu = job.resources.get("nvidia_gpu")
        accelerators = []

        # https://cloud.google.com/compute/docs/gpus#introduction
        if gpu is not None:
            # Case 1: it's a number
            gpu_count = 1
            try:
                gpu_count = int(gpu)
                gpu = None
            except ValueError:
                pass

            # Add the gpu. Thi assumes just one type, for a certain count
            accelerator = batch_v1.AllocationPolicy.Accelerator()
            accelerator.count = gpu_count

            # This is always required
            if gpu is None:
                gpu = "nvidia-tesla-t4"
            accelerator.type_ = gpu

            # This could eventually support adding to the list
            # but currently does not
            accelerators.append(accelerator)
        return accelerators

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
        return os.path.relpath(self.workflow.main_snakefile, os.getcwd())

    async def check_active_jobs(self, active_jobs: List[SubmittedJobInfo]):
        """
        Check the status of active jobs.
        """
        # Loop through active jobs and act on status
        for j in active_jobs:
            jobid = j.external_jobid
            request = batch_v1.GetJobRequest(name=jobid)

            # Aux logs are consistently here
            aux_logs = [j.aux["logfile"]]
            last_seen = j.aux["last_seen"]

            try:
                response = self.batch.get_job(request=request)
            except DeadlineExceeded:
                msg = f"Google Batch job '{j.external_jobid}' exceeded deadline. "
                self.report_job_error(j, msg=msg, aux_logs=aux_logs)
                yield j

            self.logger.info(f"Job {jobid} has state {response.status.state.name}")
            for event in response.status.status_events:
                if not last_seen or event.event_time.nanosecond > last_seen:
                    self.logger.info(f"{event.type_}: {event.description}")
                    last_seen = event.event_time.nanosecond

            # Update last seen for next time (TODO not sure this is sticking)
            j.aux["last_seen"] = last_seen

            # Possible statuses:
            # RUNNING
            # SCHEDULED
            # QUEUED
            # STATE_UNSPECIFIED
            # SUCCEEDED
            # FAILED
            # DELETION_IN_PROGRESS
            if response.status.state.name in ["FAILED", "SUCCEEDED"]:
                self.save_finished_job_logs(j)

            if response.status.state.name == "FAILED":
                msg = f"Google Batch job '{j.external_jobid}' failed. "
                self.report_job_error(j, msg=msg, aux_logs=aux_logs)

            elif response.status.state.name == "SUCCEEDED":
                self.report_job_success(j)

            # Otherwise, we are queued / scheduled / running, etc.
            else:
                yield j

    def save_finished_job_logs(
        self,
        job_info: SubmittedJobInfo,
        sleeps=60,
        page_size=1000,
    ):
        """
        Download logs using Google Cloud Logging API and save
        them locally. Since tail logging does not work, this function
        is run only at the end of the job.
        """
        job_uid = job_info.aux["batch_job"].uid
        filter_query = f"labels.job_uid={job_uid}"
        logfname = job_info.aux["logfile"]

        log_client = logging.Client(project=self.executor_settings.project)
        logger = log_client.logger("batch_task_logs")

        def attempt_log_save(fname, query, page_size):
            with open(fname, "w", encoding="utf-8") as logfile:
                for log_entry in logger.list_entries(
                    filter_=query,
                    page_size=page_size,
                ):
                    logfile.write(str(log_entry.payload) + "\n")

        self.logger.info(f"Saving logs for Batch job {job_uid} to {logfname}.")

        try:
            attempt_log_save(logfname, filter_query, page_size)
        except ResourceExhausted:
            self.logger.warning(
                "Too many requests to Google Logging API.\n"
                + f"Skipping logs for job {job_uid} and sleeping for {sleeps}s."
            )
            time.sleep(sleeps)

            self.logger.warning(
                f"Trying to retrieve logs for Batch job {job_uid} once more."
            )
            try:
                attempt_log_save(logfname, filter_query, page_size)
            except ResourceExhausted:
                self.logger.warning(
                    "Retry to retrieve logs failed, "
                    + f"the log file {logfname} might be incomplete."
                )
        except Exception as e:
            self.logger.warning(
                f"Failed to retrieve logs for Batch job {job_uid}: {str(e)}"
            )

    def cancel_jobs(self, active_jobs: List[SubmittedJobInfo]):
        """
        Cancel all active jobs. This method is called when snakemake is interrupted.
        """
        for job in active_jobs:
            jobid = job.external_jobid
            reason = f"User requested cancel for {jobid}"
            request = batch_v1.DeleteJobRequest(name=jobid, reason=reason)
            operation = self.batch.delete_job(request=request)
            self.logger.info(f"Waiting for job {jobid} to cancel...")
            response = operation.result()
            self.logger.info(response)

        # Ensure we cleanup cache, etc.
        self.shutdown()

    def shutdown(self):
        """
        Shutdown deletes build packages if the user didn't request to clean
        up the cache. At this point we've already cancelled running jobs.
        """

        # Call parent shutdown
        super().shutdown()
