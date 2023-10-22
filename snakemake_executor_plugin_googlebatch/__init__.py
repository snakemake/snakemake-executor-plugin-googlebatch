from dataclasses import dataclass, field
from typing import Optional

from snakemake_interface_executor_plugins.settings import (
    CommonSettings,
    ExecutorSettingsBase,
)
from .executor import GoogleBatchExecutor as Executor  # noqa


# Optional:
# Define additional settings for your executor.
# They will occur in the Snakemake CLI as --<executor-name>-<param-name>
# Omit this class if you don't need any.
# Make sure that all defined fields are Optional and specify a default value
# of None or anything else that makes sense in your case.
@dataclass
class ExecutorSettings(ExecutorSettingsBase):
    project: Optional[str] = field(
        default=None,
        metadata={
            "help": "The name of the Google Project.",
            # Request that setting is also available for specification in environment
            # SNAKEMAKE_GOOGLEBATCH_PROJECT
            "env_var": True,
            # Optionally specify that setting is required when the executor is in use.
            "required": True,
        },
    )

    region: Optional[str] = field(
        default=None,
        metadata={
            "help": "The name of the Google Project region (e.g., us-central1)",
            "env_var": True,
            "required": True,
        },
    )

    # mpitune configurations are validated on c2 and c2d instances only.
    machine_type: Optional[str] = field(
        default="c2-standard-4",
        metadata={
            "help": "Google Cloud machine type or VM (mpitune on c2 and c2d family)",
            "env_var": False,
            "required": False,
        },
    )

    labels: Optional[str] = field(
        default="",
        metadata={
            "help": "Comma separated key value pairs to label job "
            "(e.g., model=a3,stage=test)",
            "env_var": False,
            "required": False,
        },
    )

    # This could also be batch-centos, batch-debian, batch-cos
    image_family: Optional[str] = field(
        default="hpc-centos-7",
        metadata={
            "help": "Google Cloud image family (defaults to hpc-centos-7)",
            "env_var": False,
            "required": False,
        },
    )

    container: Optional[str] = field(
        default=None,
        metadata={
            "help": "A snakemake container for batch-cos image family.",
            "env_var": False,
            "required": False,
        },
    )

    image_project: Optional[str] = field(
        default="cloud-hpc-image-public",
        metadata={
            "help": "Selected image project (defaults cloud-hpc-image-public)",
            "env_var": False,
            "required": False,
        },
    )

    bucket: Optional[str] = field(
        default=None,
        metadata={
            "help": "A bucket to mount with snakemake data",
            "env_var": True,
            "required": True,
        },
    )

    work_tasks: Optional[str] = field(
        default=1,
        metadata={
            "help": "The default number of work tasks (these are NOT MPI ranks)",
            "env_var": False,
            "required": False,
        },
    )

    cpu_milli: Optional[str] = field(
        default=1000,
        metadata={
            "help": "Milliseconds per cpu-second",
            "env_var": False,
            "required": False,
        },
    )

    cpu_milli: Optional[str] = field(
        default=1000,
        metadata={
            "help": "Milliseconds per cpu-second",
            "env_var": False,
            "required": False,
        },
    )

    work_tasks_per_node: Optional[str] = field(
        default=1,
        metadata={
            "help": "The default number of work tasks per node (NOT MPI ranks)",
            "env_var": False,
            "required": False,
        },
    )

    memory: Optional[str] = field(
        default=1000,
        metadata={
            "help": "Memory in MiB",
            "env_var": False,
            "required": False,
        },
    )

    mount_path: Optional[str] = field(
        default="/mnt/share",
        metadata={
            "help": "Mount path for Google bucket (if defined)",
            "env_var": False,
            "required": False,
        },
    )

    retry_count: Optional[str] = field(
        default=1,
        metadata={
            "help": "Retry count (default to 1)",
            "env_var": False,
            "required": False,
        },
    )

    max_run_duration: Optional[str] = field(
        default="3600s",
        metadata={
            "help": "Maximum run duration, string (e.g., 3600s)",
            "env_var": False,
            "required": False,
        },
    )

    keep_source_cache: Optional[bool] = field(
        default=False,
        metadata={
            "help": "Keep the source cache of workflows in Google "
            "by --default-remote-prefix/{source}/{cache}. Each workflow working "
            "directory is compressed to a .tar.gz, named by the hash of the "
            "contents, and kept in Google Cloud Storage. By default, the caches "
            "are deleted at the shutdown step of the workflow.",
            "env_var": False,
            "required": False,
        },
    )

    snippets: Optional[str] = field(
        default=None,
        metadata={
            "help": "One or more snippets to add to the Google Batch task setup",
            "env_var": False,
            "required": False,
        },
    )


# Required:
# Common settings shared by various executors.
common_settings = CommonSettings(
    pass_envvar_declarations_to_cmd=True,
    non_local_exec=True,
    implies_no_shared_fs=True,
)
