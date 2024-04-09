# Templates for the command writer

import snakemake_executor_plugin_googlebatch.snippet as sniputil

write_snakefile = """
#!/bin/bash
snakefile_path=$(realpath %s)
snakefile_dir=$(dirname $snakefile_path)
mkdir -p $snakefile_dir || true
cat <<EOF > $snakefile_path
%s
EOF
echo "Snakefile is at $snakefile_path"
cat $snakefile_path
"""

write_entrypoint = """
#!/bin/bash

mkdir -p /tmp/workdir
cat <<EOF > /tmp/workdir/entrypoint.sh
%s

# https://github.com/boto/botocore/issues/3111
python3 -m pip install boto3==1.33.11
python3 -m pip install urllib3==1.26.17
EOF
chmod +x /tmp/workdir/entrypoint.sh
cat /tmp/workdir/entrypoint.sh
"""

snakemake_base_environment = """export HOME=/root
export PATH=/opt/conda/bin:${PATH}
export LANG=C.UTF-8
export SHELL=/bin/bash
"""

snakemake_centos_install = (
    snakemake_base_environment
    + """
sudo yum update -y
sudo yum install -y wget bzip2 ca-certificates gnupg2 squashfs-tools git
"""
)

snakemake_debian_install = (
    snakemake_base_environment
    + """
sudo apt-get update -y
sudo apt-get install -y wget bzip2 ca-certificates gnupg2 squashfs-tools git
"""
)

install_snakemake = """
echo "I am batch index ${BATCH_TASK_INDEX}"

export PATH=/opt/conda/bin:${PATH}
if [[ "${BATCH_TASK_INDEX}" == "0" ]]; then
  repo=https://raw.githubusercontent.com/snakemake/snakemake-executor-plugin-googlebatch
  path=main/scripts/install-snek.sh
  wget ${repo}/${path}
  chmod +x ./install-snek.sh
  workdir=$(pwd)
  url=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
  wget ${url} -O ./miniconda.sh
  chmod +x ./miniconda.sh
  bash ./miniconda.sh -b -u -p /opt/conda
  rm -rf ./miniconda.sh

  # Failed building wheel for datrie python 3.12
  conda install datrie --yes
  which python
  /opt/conda/bin/python --version
  ./install-snek.sh https://github.com/snakemake/snakemake-storage-plugin-gcs
  ./install-snek.sh https://github.com/snakemake/snakemake
  touch /tmp/snakemake-install-done.txt
else
  while [ ! -f snakemake-install-done.txt ]
  do
    sleep 5
  done
  echo "Snakemake install is done"
fi

cd ${workdir}
"""

check_for_snakemake = (
    snakemake_base_environment
    + """
echo $(pwd)
ls
which snakemake || whereis snakemake
"""
)


class CommandWriter:
    """
    A command writer knows how to write a Snakemake command

    This is intended for Google Batch operating systems.
    """

    def __init__(
        self,
        command=None,
        snakefile=None,
        snippets=None,
        settings=None,
        resources=None,
        snakefile_path=None,
    ):
        self.command = command

        # This is the contents of the snakefile
        self.snakefile = snakefile
        self.resources = resources
        self.settings = settings
        self.snakefile_path = snakefile_path

        # Prepare (and validate) any provided snippets for the job
        self.load_snippets(snippets)

    def load_snippets(self, spec):
        """
        Given a spec, load into snippets for the job (setup and run)

        We also validate here (early on) to exit early if needed
        """
        # Settings are important to provide as they have params
        self.snippets = sniputil.SnippetGroup(spec, self.settings, self.resources)
        self.snippets.validate()

    def run(self):
        """
        Write the command script. This is likely shared.

        We allow one or more pre-commands (e.g., to download artifacts)
        """
        command = "\n"

        # Ensure we check for snakemake
        command += check_for_snakemake

        # If we have a snippet group, add snippets before installing snakemake
        if self.snippets:
            command += self.snippets.render_run(self.command)

        # Don't include the main command twice
        if self.snippets.has_run_command_snippet:
            return command
        return command + "\n" + self.command

    def setup(self):
        """
        Derive the correct setup command based on the family.
        """
        pass

    def write_snakefile(self):
        """
        Return tempalted snakefile. We do this in a separate step so
        a later container step can use it.
        """
        return write_snakefile % (self.snakefile_path, self.snakefile)

    def _template_setup(self, template, use_container=False):
        """
        Shared logic to template the setup command.
        """
        command = template

        # If we have a snippet group, add snippets before installing snakemake
        if self.snippets:
            command += self.snippets.render_setup(self.command)

        # If we don't use container, install snakemkae to VM
        if not use_container:
            command += install_snakemake
        return command


class COSWriter(CommandWriter):
    """
    A custom writer for a cos-based family.
    """

    def setup(self):
        """
        Setup for the container operating system means writing
        the entrypoint. We do not use any snippets here, using
        a container assumes what the user needs is in the
        container.
        """
        return write_entrypoint % self.command


class DebianWriter(CommandWriter):
    """
    A custom writer for a debian-based family.
    """

    def setup(self):
        return self._template_setup(snakemake_debian_install)


class CentosWriter(CommandWriter):
    """
    A custom writer for a centos-based family.
    """

    def setup(self):
        return self._template_setup(snakemake_centos_install)


def get_writer(family):
    """
    Instantiate a writer based on a family.
    """
    # https://cloud.google.com/batch/docs/view-os-images
    if "batch-cos" in family:
        return COSWriter
    if "debian" in family:
        return DebianWriter
    # Google cloud seems to prefer rocky/centos, use as default
    return CentosWriter
