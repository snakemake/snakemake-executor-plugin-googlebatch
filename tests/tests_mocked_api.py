from typing import Optional
from unittest.mock import patch

from google.cloud.batch_v1.types import Job, JobStatus

import snakemake.common.tests
import snakemake.settings
from snakemake_executor_plugin_googlebatch import ExecutorSettings
from snakemake_interface_executor_plugins.settings import ExecutorSettingsBase

from tests import TestWorkflowsBase


class TestWorkflowsMocked(TestWorkflowsBase):
    __test__ = True

    @patch(
        "google.cloud.batch_v1.BatchServiceClient.create_job",
        return_value=Job(name="foo"),
        autospec=True,
    )
    @patch(
        "google.cloud.batch_v1.BatchServiceClient.get_job",
        return_value=Job(status=JobStatus(state=JobStatus.State.SUCCEEDED)),
        autospec=True,
    )
    def run_workflow(*args, **kwargs):
        super().run_workflow(*args, **kwargs)
