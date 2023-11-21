from unittest.mock import AsyncMock, MagicMock, patch

from google.cloud.batch_v1.types import Job, JobStatus

from tests import TestWorkflowsBase


class TestWorkflowsMocked(TestWorkflowsBase):
    __test__ = True

    @patch(
        "google.cloud.batch_v1.BatchServiceClient.create_job",
        new=MagicMock(
            return_value=Job(name="foo"),
            autospec=True,
        ),
    )
    @patch(
        "google.cloud.batch_v1.BatchServiceClient.get_job",
        new=MagicMock(
            return_value=Job(status=JobStatus(state=JobStatus.State.SUCCEEDED)),
            autospec=True,
        ),
    )
    @patch(
        "snakemake.dag.DAG.check_and_touch_output",
        new=AsyncMock(autospec=True),
    )
    @patch(
        "snakemake_storage_plugin_s3.StorageObject.managed_size",
        new=AsyncMock(autospec=True, return_value=0),
    )
    def run_workflow(self, *args, **kwargs):
        super().run_workflow(*args, **kwargs)
