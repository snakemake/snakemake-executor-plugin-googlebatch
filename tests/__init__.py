import os

import snakemake.common.tests
import snakemake.settings.types
from snakemake_interface_executor_plugins.settings import ExecutorSettingsBase

from snakemake_executor_plugin_googlebatch import ExecutorSettings

# from snakemake_interface_storage_plugins.settings import StorageProviderSettingsBase


class TestWorkflowsBase(snakemake.common.tests.TestWorkflowsMinioPlayStorageBase):
    def get_executor(self) -> str:
        return "googlebatch"

    def get_executor_settings(self) -> ExecutorSettingsBase:
        # Allow custom one-off project/region from the environment
        project = os.environ.get("SNAKEMAKE_GOOGLEBATCH_PROJECT") or "snakemake-testing"
        region = os.environ.get("SNAKEMAKE_GOOGLEBATCH_REGION") or "us-central1"

        # instatiate ExecutorSettings of this plugin as appropriate
        return ExecutorSettings(
            project=project,
            region=region,
        )

    def get_assume_shared_fs(self):
        return False

    def get_remote_execution_settings(
        self,
    ) -> snakemake.settings.types.RemoteExecutionSettings:
        return snakemake.settings.types.RemoteExecutionSettings(
            seconds_between_status_checks=1,
            envvars=self.get_envvars(),
        )

    @property
    def endpoint_url(self):
        return os.getenv("SNAKEMAKE_GOOGLEBATCH_S3_ENDPOINT_URL", super().endpoint_url)
