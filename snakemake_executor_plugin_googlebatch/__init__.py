from dataclasses import dataclass, field
from typing import Optional

from snakemake_interface_executor_plugins.settings import (
    CommonSettings,
    ExecutorSettingsBase,
)
from .executor import GoogleBatchExecutor as Executor  # noqa
import urllib3

urllib3.disable_warnings()


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

    container: Optional[str] = field(
        default=None,
        metadata={
            "help": "A custom container for use with Google Batch COS",
            "env_var": False,
            "required": False,
        },
    )

    docker_password: Optional[str] = field(
        default=None,
        metadata={
            "help": "A docker registry password for COS if credentials are required",
            "env_var": True,
            "required": False,
        },
    )

    docker_username: Optional[str] = field(
        default=None,
        metadata={
            "help": "A docker registry username for COS if credentials are required",
            "env_var": True,
            "required": False,
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
    # For COS, family is batch-<os>-<version>-official, e.g.,
    # batch-debian-11-official
    image_family: Optional[str] = field(
        default="hpc-centos-7",
        metadata={
            "help": "Google Cloud image family (defaults to hpc-centos-7)",
            "env_var": False,
            "required": False,
        },
    )

    # for cos, should be batch-custom-image
    image_project: Optional[str] = field(
        default="cloud-hpc-image-public",
        metadata={
            "help": "Selected image project (defaults cloud-hpc-image-public)",
            "env_var": False,
            "required": False,
        },
    )

    work_tasks: Optional[int] = field(
        default=1,
        metadata={
            "help": "The default number of work tasks (these are NOT MPI ranks)",
            "env_var": False,
            "required": False,
        },
    )

    cpu_milli: Optional[int] = field(
        default=1000,
        metadata={
            "help": "Milliseconds per cpu-second",
            "env_var": False,
            "required": False,
        },
    )

    # Note that additional disks can be added, but this is not exposed yet
    boot_disk_gb: Optional[int] = field(
        default=None,
        metadata={
            "help": "Boot disk size (GB)",
            "env_var": False,
            "required": False,
        },
    )

    network: Optional[str] = field(
        default=None,
        metadata={
            "help": "The URL of an existing network resource",
            "env_var": False,
            "required": False,
        },
    )

    subnetwork: Optional[str] = field(
        default=None,
        metadata={
            "help": "The URL of an existing subnetwork resource",
            "env_var": False,
            "required": False,
        },
    )

    service_account: Optional[str] = field(
        default=None,
        metadata={
            "help": "The email of a customer compute service account",
            "env_var": True,
            "required": False,
        },
    )

    # local SSD uses type "local-ssd".
    # Also "pd-balanced", "pd-extreme", "pd-ssd", "pd-standard"
    boot_disk_type: Optional[str] = field(
        default=None,
        metadata={
            "help": "Boot disk type. (e.g., gcloud compute disk-types list)",
            "env_var": False,
            "required": False,
        },
    )

    # if not set, defaults to family
    boot_disk_image: Optional[str] = field(
        default=None,
        metadata={
            "help": "Boot disk image (e.g., batch-debian, bath-centos)",
            "env_var": False,
            "required": False,
        },
    )

    work_tasks_per_node: Optional[int] = field(
        default=1,
        metadata={
            "help": "The default number of work tasks per node (NOT MPI ranks)",
            "env_var": False,
            "required": False,
        },
    )

    memory: Optional[int] = field(
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

    retry_count: Optional[int] = field(
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
# IMPORTANT: this is set to artifically be False / False
# because the storage GS is not working / buggy
common_settings = CommonSettings(
    # TODO: we should rather pass envs to the container I guess
    pass_envvar_declarations_to_cmd=True,
    non_local_exec=True,
    implies_no_shared_fs=True,
    job_deploy_sources=True,
    pass_default_storage_provider_args=True,
    pass_default_resources_args=True,
    auto_deploy_default_storage_provider=True,
)
