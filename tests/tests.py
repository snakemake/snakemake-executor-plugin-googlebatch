from typing import Optional

import snakemake.common.tests
from snakemake_executor_plugin_googlebatch import ExecutorSettings
from snakemake_interface_executor_plugins.settings import ExecutorSettingsBase
from snakemake_interface_storage_plugins.settings import StorageProviderSettingsBase

BUCKET_NAME = "change-me"


class TestWorkflowsBase(snakemake.common.tests.TestWorkflowsBase):
    __test__ = True

    def get_executor(self) -> str:
        return "googlebatch"

    def get_default_storage_provider_settings(self):
        return StorageProviderSettingsBase()

    def get_executor_settings(self) -> Optional[ExecutorSettingsBase]:
        # instatiate ExecutorSettings of this plugin as appropriate
        return ExecutorSettings(
            keep_source_cache=False,
            bucket=BUCKET_NAME,
        )

    def get_default_storage_provider(self) -> Optional[str]:
        # Return name of default remote provider if required for testing,
        # otherwise None.
        return None

    def get_default_storage_prefix(self) -> Optional[str]:
        # Return default remote prefix if required for testing,
        # otherwise None.
        return BUCKET_NAME
