import asyncio
import logging
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
import snakemake
from google.cloud import batch_v1
from google.cloud.batch_v1.types import job as gcp_job
from snakemake.jobs import Job
from snakemake_interface_executor_plugins.executors.base import SubmittedJobInfo

from snakemake_executor_plugin_googlebatch import ExecutorSettings
from snakemake_executor_plugin_googlebatch.executor import GoogleBatchExecutor


@pytest.fixture(scope="module", autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def executor_settings():
    settings = Mock(spec_set=ExecutorSettings)
    settings.project = "test-project"
    settings.region = "us-central1"
    return settings


@pytest.fixture
def workflow():
    workflow = Mock(spec_set=snakemake.workflow.Workflow)
    workflow.workdir = "/tmp/workdir"
    workflow.persistence.path = "/tmp/workdir"

    workflow.remote_execution_settings.jobname = "sm-{jobid}"
    # The snakemake 'container_image', not the one defined in our ExecutorSettings
    workflow.remote_execution_settings.container_image = "snakemake/snakemake:latest"
    workflow.remote_execution_settings.preemptible_rules.is_preemptible.return_value = (
        False
    )
    workflow.remote_execution_settings.seconds_between_status_checks = 10
    workflow.remote_execution_settings.max_status_checks_per_second = 1

    workflow.executor_settings = ExecutorSettings()
    workflow.executor_settings.container = "snakemake/snakemake:latest"
    workflow.executor_settings.entrypoint = "/bin/true"
    workflow.executor_settings.docker_username = None
    workflow.executor_settings.docker_password = None

    workflow.storage_settings.shared_fs_usage = []
    workflow.group_settings.local_groupid = 1
    workflow.spawned_job_args_factory.general_args.return_value = "--dry-run"
    workflow.spawned_job_args_factory.precommand.return_value = ""
    workflow.spawned_job_args_factory.envvars.return_value = {}

    with tempfile.NamedTemporaryFile() as f:
        workflow.main_snakefile = f.name
        yield workflow


@pytest.fixture
def job():
    job = Mock(spec_set=Job)
    job.name = "test-job"
    job.resources = {"googlebatch_image_family": "batch-cos-stable"}
    job.is_group.return_value = False
    job.rules = []
    job.rule.name = "test-rule"

    def logfile_suggestion(path):
        return path

    job.logfile_suggestion = logfile_suggestion
    return job


@pytest.fixture
def executor(workflow, executor_settings):
    with (
        patch("google.cloud.batch_v1.BatchServiceClient"),
        patch("builtins.open") as mock_open,
    ):
        # Configure the mock to support context manager protocol
        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        executor = GoogleBatchExecutor(workflow=workflow, logger=MagicMock())
        with patch.object(executor, "get_job_args", return_value=[]):
            with patch.object(
                executor,
                "save_finished_job_logs",
            ):
                with patch.object(
                    executor,
                    "report_job_success",
                ):
                    yield executor


class TestGoogleBatchExecutor:
    def test_get_param_from_resources(self, executor, job):
        job.resources = {"googlebatch_memory": 2048}
        executor.executor_settings.memory = 1024
        assert executor.get_param(job, "memory") == 2048

    def test_get_param_from_settings(self, executor, job):
        executor.executor_settings.memory = 1024
        assert executor.get_param(job, "memory") == 1024

    def test_get_task_resources(self, executor, job):
        job.resources = {"googlebatch_cpu_milli": 1000, "googlebatch_memory": 2048}
        resources = executor.get_task_resources(job)
        assert resources.cpu_milli == 1000
        assert resources.memory_mib == 2048

    def test_get_labels(self, executor, job):
        job.resources = {"googlebatch_labels": "key1=value1,key2=value2"}
        labels = executor.get_labels(job)
        assert "snakemake-job" in labels
        assert labels["key1"] == "value1"
        assert labels["key2"] == "value2"

    def test_add_storage(self, executor, job):
        job.resources = {
            "googlebatch_bucket": "test-bucket",
            "googlebatch_mount_path": "/mnt/data",
        }
        task = batch_v1.TaskSpec()
        executor.add_storage(job, task)
        assert len(task.volumes) == 1
        assert task.volumes[0].gcs.remote_path == "test-bucket"
        assert task.volumes[0].mount_path == "/mnt/data"

    def test_generate_jobid(self, executor, job):
        jobid = executor.generate_jobid(job)
        assert job.name.replace("_", "-").replace(".", "")[:50] in jobid
        assert (
            len(jobid) == len(job.name.replace("_", "-").replace(".", "")[:50]) + 7
        )  # name + "-" + 6 chars

    def test_is_container_job(self, executor, job):
        job.resources = {"googlebatch_image_family": "batch-cos-stable"}
        assert executor.is_container_job(job) is True

        job.resources = {"googlebatch_image_family": "batch-centos"}
        assert executor.is_container_job(job) is False

    def test_fix_job_name(self, executor):
        assert executor.fix_job_name("test_job.name") == "test-jobname"
        assert executor.fix_job_name("a" * 60) == "a" * 50  # Test truncation

    def test_project_parent(self, executor, job):
        job.resources = {
            "googlebatch_project": "my-project",
            "googlebatch_region": "us-west1",
        }
        parent = executor.project_parent(job)
        assert parent == "projects/my-project/locations/us-west1"

    @patch("snakemake_executor_plugin_googlebatch.executor.cmdutil.get_writer")
    def test_get_command_writer(self, mock_get_writer, executor, job):
        mock_writer_class = Mock()
        mock_get_writer.return_value = mock_writer_class
        job.resources = {"googlebatch_image_family": "batch-cos-stable"}

        writer = executor.get_command_writer(job)
        assert writer == mock_writer_class.return_value
        mock_get_writer.assert_called_once_with("batch-cos-stable")

    def test_get_container_without_container_job(self, executor, job):
        job.resources = {"googlebatch_image_family": "batch-centos"}
        container = executor.get_container(job)
        assert container is None

    @patch("snakemake_executor_plugin_googlebatch.executor.cmdutil.get_writer")
    def test_run_job(self, mock_get_writer, executor, job):
        # Setup mocks
        mock_writer = Mock()
        mock_writer.setup.return_value = "setup command"
        mock_writer.run.return_value = "run command"
        mock_writer.write_snakefile.return_value = "snakefile content"
        mock_get_writer.return_value = Mock(return_value=mock_writer)

        job.resources = {
            "googlebatch_image_family": "batch-cos-stable",
            "googlebatch_retry_count": 3,
            "googlebatch_max_run_duration": "3600s",
            "googlebatch_container": "snakemake/snakemake:latest",
        }

        # Mock batch client response
        mock_created_job = Mock()
        mock_created_job.name = "test-job-name"
        mock_created_job.uid = "test-uid"
        executor.batch.create_job.return_value = mock_created_job

        executor.run_job(job)

        # Verify job was submitted
        executor.batch.create_job.assert_called_once()

    def test_get_accelerators_with_gpu_count(self, executor, job):
        job.resources = {"nvidia_gpu": "2"}
        accelerators = executor.get_accelerators(job)
        assert len(accelerators) == 1
        assert accelerators[0].count == 2
        assert accelerators[0].type_ == "nvidia-tesla-t4"

    def test_get_accelerators_with_gpu_type(self, executor, job):
        job.resources = {"nvidia_gpu": "nvidia-tesla-k80"}
        accelerators = executor.get_accelerators(job)
        assert len(accelerators) == 1
        assert accelerators[0].count == 1
        assert accelerators[0].type_ == "nvidia-tesla-k80"

    def test_get_boot_disk(self, executor, job):
        job.resources = {
            "googlebatch_boot_disk_image": "projects/test-project/global/images/test-image",
            "googlebatch_boot_disk_gb": 100,
            "googlebatch_boot_disk_type": "pd-ssd",
        }
        boot_disk = executor.get_boot_disk(job)
        assert boot_disk.image == "projects/test-project/global/images/test-image"
        assert boot_disk.size_gb == 100
        assert boot_disk.type_ == "pd-ssd"

    def test_get_network_policy(self, executor, job):
        job.resources = {
            "googlebatch_network": "projects/test-project/global/networks/test-network",
            "googlebatch_subnetwork": "projects/test-project/regions/us-central1/subnetworks/test-subnetwork",
        }
        policy = executor.get_network_policy(job)
        assert (
            policy.network_interfaces[0].network
            == "projects/test-project/global/networks/test-network"
        )
        assert (
            policy.network_interfaces[0].subnetwork
            == "projects/test-project/regions/us-central1/subnetworks/test-subnetwork"
        )

    def test_get_service_account(self, executor, job):
        job.resources = {
            "googlebatch_service_account": "test-service-account@test-project.iam.gserviceaccount.com"
        }
        service_account = executor.get_service_account(job)
        assert (
            service_account.email
            == "test-service-account@test-project.iam.gserviceaccount.com"
        )

    @patch("snakemake_executor_plugin_googlebatch.executor.cmdutil.get_writer")
    def test_check_active_jobs_succeeded(self, mock_get_writer, executor, job):
        # Setup mock job
        mock_batch_job = Mock()
        submitted_job = SubmittedJobInfo(
            job=job,
            external_jobid="projects/test-project/locations/us-central1/jobs/test-job",
            aux={
                "logfile": "/tmp/test.log",
                "last_seen": None,
                "batch_job": mock_batch_job,
            },
        )

        # Setup mock batch response
        mock_response = gcp_job.Job()
        mock_response.status.state = gcp_job.JobStatus.State.SUCCEEDED
        executor.batch.get_job.return_value = mock_response

        # Create async generator and get result
        async def collect_results():
            results = []
            async for result in executor.check_active_jobs([submitted_job]):
                results.append(result)
            return results

        results = asyncio.run(collect_results())

        # Should be empty since job succeeded
        assert len(results) == 0
        executor.batch.get_job.assert_called_once()

    @patch("snakemake_executor_plugin_googlebatch.executor.cmdutil.get_writer")
    def test_check_active_jobs_failed(self, mock_get_writer, executor, job):
        # Setup mock job
        submitted_job = SubmittedJobInfo(
            job=job,
            external_jobid="projects/test-project/locations/us-central1/jobs/test-job",
            aux={
                "logfile": "/tmp/test.log",
                "last_seen": None,
            },
        )

        # Setup mock batch response
        mock_response = gcp_job.Job()
        mock_response.status.state = gcp_job.JobStatus.State.FAILED
        executor.batch.get_job.return_value = mock_response

        # Create async generator and get result
        async def collect_results():
            collected = []
            async for result in executor.check_active_jobs([submitted_job]):
                collected.append(result)
            return collected

        results = asyncio.run(collect_results())

        # Should be empty since job failed and was reported
        assert len(results) == 0
        executor.batch.get_job.assert_called_once()

    def test_cancel_jobs(self, executor, job):
        submitted_job = SubmittedJobInfo(
            job=job,
            external_jobid="projects/test-project/locations/us-central1/jobs/test-job",
        )

        mock_operation = Mock()
        mock_operation.result.return_value = "cancelled"
        executor.batch.delete_job.return_value = mock_operation

        executor.cancel_jobs([submitted_job])

        executor.batch.delete_job.assert_called_once()
