
# Templates for the command writer

write_snakefile = """
cat <<EOF > ./Snakefile
%s
EOF
cat ./Snakefile
"""

snakemake_base_environment = """
export HOME=/root
export PATH=/opt/conda/bin:${PATH}
export LANG=C.UTF-8
export SHELL=/bin/bash
"""

snakemake_centos_install = snakemake_base_environment + """
sudo yum update -y
sudo yum install -y wget bzip2 ca-certificates gnupg2 squashfs-tools git
"""

snakemake_debian_install = snakemake_base_environment + """
sudo apt-get update -y
sudo apt-get install -y wget bzip2 ca-certificates gnupg2 squashfs-tools git
"""

install_snakemake = """
# Only the main job should install conda (rest can use it)
echo "I am batch index ${BATCH_TASK_INDEX}"
export PATH=/opt/conda/bin:${PATH}
if [ $BATCH_TASK_INDEX = 0 ] && [ ! -d "/opt/conda" ] ; then
    workdir=$(pwd)
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda.sh
    chmod +x ./miniconda.sh
    bash ./miniconda.sh -b -u -p /opt/conda
    rm -rf ./miniconda.sh
    conda config --system --set channel_priority strict 
    which python
    /opt/conda/bin/python --version
    git clone --depth 1 https://github.com/snakemake/snakemake-interface-common /tmp/snakemake-common
    cd /tmp/snakemake-common
    /opt/conda/bin/python -m pip install .
    git clone --depth 1 https://github.com/snakemake/snakemake-interface-executor-plugins /tmp/snakemake-plugin
    cd /tmp/snakemake-plugin
    /opt/conda/bin/python -m pip install .
    git clone --depth 1 https://github.com/snakemake/snakemake /tmp/snakemake
    cd /tmp/snakemake
    /opt/conda/bin/python -m pip install .
    cd ${workdir}
fi
"""

run_snakemake = snakemake_base_environment + """
$(pwd)
ls
which snakemake || whereis snakemake
"""


class CommandWriter:
    """
    A command writer knows how to write a Snakemake command

    This is intended for Google Batch operating systems.
    """
    def __init__(self, command=None, container=None, snakefile=None):
        self.command = command 
        self.container = container

        # This is the contents of the snakefile and not the path
        self.snakefile = snakefile

    def run_command(self):
        """
        Write the command script for debian
        """
        return run_snakemake + self.command

    def setup_debian(self):
        """
        Write the setup command script for debian
        """
        return self._template_setup(snakemake_debian_install)

    def setup_centos(self):
        """
        Write the setup command script for debian
        """
        return self._template_setup(snakemake_centos_install)

    def _template_setup(self, template):
        """
        Shared logic to template the setup command (debian or centos)
        """
        command = template
        command += write_snakefile % self.snakefile 
        command += install_snakemake
        return command

    def for_cos(self):
        """
        Write the command script for cos.

        For this command we assume the container has python as python3
        TODO not tested yet
        """
        command = write_snakefile % self.snakefile
        docker = "docker run -it -v $PWD/Snakefile:./Snakefile {self.container} {self.command}"
        command += docker
        return command


def derive_setup_command(container, family, snakefile):
    """
    Derive the setup command (between the barrier and the main task)
    """
    writer = CommandWriter(container=container, snakefile=snakefile)
    if family == "batch-cos":
        return writer.setup_cos()

    # hpc-centos-<x> or batch-centos
    if "centos" in family:
        return writer.setup_centos()

    # batch-debian
    return writer.setup_debian()    


def derive_command(command, family):
    """
    Given a job command, derive command based on family.
    """
    writer = CommandWriter(command)    
    if family == "batch-cos":
        return writer.for_cos()
    return writer.run_command()