# Templates for the command writer

import snakemake_executor_plugin_googlebatch.snippet as sniputil

write_snakefile = """cat <<EOF > ./Snakefile
%s
EOF
cat ./Snakefile
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
# Only the main job should install conda (rest can use it)
echo "I am batch index ${BATCH_TASK_INDEX}"
export PATH=/opt/conda/bin:${PATH}
if [ $BATCH_TASK_INDEX = 0 ] && [ ! -d "/opt/conda" ] ; then
    workdir=$(pwd)
    url=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    wget ${url} -O ./miniconda.sh
    chmod +x ./miniconda.sh
    bash ./miniconda.sh -b -u -p /opt/conda
    rm -rf ./miniconda.sh
    conda config --system --set channel_priority strict
    which python
    /opt/conda/bin/python --version    
    url=https://github.com/snakemake/snakemake-storage-plugin-gs
    git clone --depth 1 ${url} /tmp/snakemake-gs
    cd /tmp/snakemake-gs
    /opt/conda/bin/python -m pip install .
    url=https://github.com/snakemake/snakemake-interface-common
    git clone --depth 1 ${url} /tmp/snakemake-common
    cd /tmp/snakemake-common
    /opt/conda/bin/python -m pip install .
    url=https://github.com/snakemake/snakemake-interface-executor-plugins
    git clone --depth 1 ${url} /tmp/snakemake-plugin
    cd /tmp/snakemake-plugin
    /opt/conda/bin/python -m pip install .
    git clone --depth 1 https://github.com/snakemake/snakemake /tmp/snakemake
    cd /tmp/snakemake
    /opt/conda/bin/python -m pip install .
    cd ${workdir}
fi
"""

check_for_snakemake = (
    snakemake_base_environment
    + """
$(pwd)
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
        container=None,
        snakefile=None,
        snippets=None,
        settings=None,
        resources=None,
    ):
        self.command = command
        self.container = container

        # This is the contents of the snakefile and not the path
        self.snakefile = snakefile
        self.resources = resources
        self.settings = settings

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

    def run(self, pre_commands=None):
        """
        Write the command script. This is likely shared.

        We allow one or more pre-commands (e.g., to download artifacts)
        """
        pre_commands = pre_commands or []
        command = ""
        for pre_command in pre_commands:
            command += pre_command + "\n"

        # Ensure we check for snakemake
        command += "\n" + check_for_snakemake

        # If we have a snippet group, add snippets before installing snakemake
        if self.snippets:
            command += self.snippets.render_run(self.command, self.container)

        # Don't include the main command twice
        if self.snippets.has_run_command_snippet:
            return command
        return command + "\n" + self.command

    def setup(self):
        """
        Derive the correct setup command based on the family.
        """
        raise NotImplementedError(f"Setup is not implemented for {self}.")

    def _template_setup(self, template, use_container=False):
        """
        Shared logic to template the setup command.
        """
        command = template
        command += write_snakefile % self.snakefile

        # If we have a snippet group, add snippets before installing snakemake
        if self.snippets:
            command += self.snippets.render_setup(self.command, self.container)

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
        We pre-pull the container so they start at the same time.
        """
        command = f"docker pull {self.container}"
        return self._template_setup(command, use_container=True)

    def run(self, pre_commands=None):
        """
        Write the run command script for cos.

        For this command we assume the container has python as python3
        """
        pre_commands = pre_commands or []
        command = ""
        for pre_command in pre_commands:
            command += pre_command + "\n"
        command += write_snakefile % self.snakefile
        volume = "$PWD/Snakefile:./Snakefile"
        docker = f"docker run -it -v {volume} {self.container} {self.command}"
        command += docker
        return command


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
