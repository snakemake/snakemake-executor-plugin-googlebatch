from snakemake_interface_common.exceptions import WorkflowError  # noqa
import snakemake_executor_plugin_googlebatch.utils as utils

from google.api_core.exceptions import NotFound
from google.api_core import retry
from google.cloud import storage
import tarfile
import shutil
import tempfile
import hashlib
import re
import os

download_snippet = """
# Download the current storage archive
url=https://github.com/rse-ops/snakemake-executor-plugin-googlebatch/blob/main/script/downloader.py
wget -O /download.py ${url}

# Download <bucket name> <package>z
python /download.py download %s %s /tmp/workdir.tar.gz
tar -xzvf /tmp/workdir.tar.gz
"""  # noqa


class BuildPackage:
    """
    A build package includes the local Snakemake directory

    We upload to a Google storage cache to be shared between steps.
    """

    def __init__(self, workflow, dag, logger):
        self.workflow = workflow
        self.dag = dag
        self.logger = logger

        # Cache bucket for workflow artifacts
        self._service = storage.Client()
        self.set_bucket()

        # Build cache package
        self.set_sources()

    def upload(self):
        """
        Upload the build source package to Google Storage.
        """

        @retry.Retry(predicate=utils.google_cloud_retry)
        def _upload():
            # Upload to temporary storage, only if doesn't exist
            self.pipeline_package = "source/cache/%s" % os.path.basename(self._package)
            blob = self.bucket.blob(self.pipeline_package)
            self.logger.debug("build-package=%s" % self.pipeline_package)
            if not blob.exists():
                blob.upload_from_filename(
                    self._package, content_type="application/gzip"
                )

        _upload()

    @property
    def download_snippet(self):
        """
        Retrieve the download snippet text that includes the bucket and package names
        """
        return download_snippet % (self.bucket.name, self.pipeline_package)

    @property
    def workdir(self):
        """
        Get the directory path for the workflow
        """
        return os.path.realpath(os.path.dirname(self.workflow.persistence.path))

    def set_bucket(self):
        """
        Get a connection to the storage bucket

        We exit on authentication issue or if the name is taken or invalid.
        """
        # Hold path to requested subdirectory and main bucket
        prefix = getattr(self.workflow.executor_settings, "bucket")
        if not prefix:
            raise WorkflowError("A bucket name is required for the workflow cache.")

        # Always get the root
        bucket_name = prefix.split("/")[0]
        self.gs_subdir = re.sub(
            f"^{bucket_name}/",
            "",
            self.workflow.storage_settings.default_storage_prefix,
        )

        # Case 1: The bucket already exists
        try:
            self.bucket = self._service.get_bucket(bucket_name)

        # Case 2: The bucket needs to be created
        except NotFound:
            self.logger.info(f"Bucket not found, creating gs://{bucket_name}")
            self.bucket = self._service.create_bucket(bucket_name)

        # Case 2: The bucket name is already taken
        except Exception as ex:
            self.logger.error(
                "Cannot get or create {} (exit code {}):\n{}".format(
                    bucket_name, ex.returncode, ex.output.decode()
                )
            )
            raise WorkflowError(
                "Cannot get or create {} (exit code {}):\n{}".format(
                    bucket_name, ex.returncode, ex.output.decode()
                ),
                ex,
            )
        self.logger.info("bucket=%s" % self.bucket.name)

    def check_source_size(self, filename, warn_size_gb=0.2):
        """
        Check the source file size.

        A helper function to check the filesize, and return the file
        to the calling function Additionally, given that we encourage these
        packages to be small, we set a warning at 200MB (0.2GB).
        """
        gb = utils.bytesto(os.stat(filename).st_size, "g")
        if gb > warn_size_gb:
            self.logger.warning(
                f"File {filename} (size {gb} GB) is greater than the {warn_size_gb} "
                f"GB suggested size. Consider uploading larger files to storage first."
            )
        return filename

    def set_sources(self):
        """
        We only add files from the working directory that are config related
        (e.g., the Snakefile or a config.yml equivalent), or checked into git.
        """
        self.workflow_sources = []

        for wfs in self.dag.get_sources():
            if os.path.isdir(wfs):
                for dirpath, _, filenames in os.walk(wfs):
                    self.workflow_sources.extend(
                        [
                            self.check_source_size(os.path.join(dirpath, f))
                            for f in filenames
                        ]
                    )
            else:
                self.workflow_sources.append(
                    self.check_source_size(os.path.abspath(wfs))
                )

    def clear(self):
        """
        Clear the cache.

        This deletes all build archive files, etc.
        """
        blob = self.bucket.blob(self._package)
        if blob.exists():
            self.logger.debug(f"Deleting blob {self._package}")
            blob.delete()

    def generate_package(self):
        """
        In order for the instance to access the working directory in storage,
        we need to upload it. This file is cleaned up at the end of the run.
        We do this, and then obtain from the instance and extract.
        """
        # Workflow sources for cloud executor must all be under same workdir root
        for filename in self.workflow_sources:
            if self.workdir not in os.path.realpath(filename):
                raise WorkflowError(
                    "All source files must be present in the working directory, "
                    "{workdir} to be uploaded to a build package that respects "
                    "relative paths, but {filename} was found outside of this "
                    "directory. Please set your working directory accordingly, "
                    "and the path of your Snakefile to be relative to it.".format(
                        workdir=self.workdir, filename=filename
                    )
                )

        # We will generate a tar.gz package, renamed by hash
        tmpname = next(tempfile._get_candidate_names())
        targz = os.path.join(tempfile.gettempdir(), "snakemake-%s.tar.gz" % tmpname)
        tar = tarfile.open(targz, "w:gz")

        # Add all workflow_sources files
        for filename in self.workflow_sources:
            arcname = filename.replace(self.workdir + os.path.sep, "")
            tar.add(filename, arcname=arcname)

        tar.close()

        # Rename based on hash, in case user wants to save cache
        hasher = hashlib.sha256()
        hasher.update(open(targz, "rb").read())
        sha256 = hasher.hexdigest()
        hash_tar = os.path.join(
            self.workflow.persistence.aux_path, f"workdir-{sha256}.tar.gz"
        )

        # Only copy if we don't have it yet, clean up if we do
        if not os.path.exists(hash_tar):
            shutil.move(targz, hash_tar)
        else:
            os.remove(targz)

        # We will clean this up at shutdown
        self._package = hash_tar
        return hash_tar
