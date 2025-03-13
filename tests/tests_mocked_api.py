from unittest.mock import AsyncMock, MagicMock, patch

from google.cloud.batch_v1.types import Job, JobStatus

from tests import TestWorkflowsBase


class TestWorkflowsMockedApi(TestWorkflowsBase):
    __test__ = True

    @patch(
        "google.cloud.batch_v1.BatchServiceClient.create_job",
        new=MagicMock(
            return_value=Job(name="foo", uid="bar"),
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
        "google.cloud.logging.Client.logger",
        new=MagicMock(
            return_value=MagicMock(list_entries=lambda filter_, page_size: []),
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
    @patch(
        # mocking has to happen in the importing module, see
        # http://www.gregreda.com/2021/06/28/mocking-imported-module-function-python
        "snakemake.jobs.wait_for_files",
        new=AsyncMock(autospec=True),
    )
    def run_workflow(self, *args, **kwargs):
        super().run_workflow(*args, **kwargs)
