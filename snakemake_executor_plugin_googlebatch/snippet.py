# Snippets to provide to the command writer

from snakemake_interface_common.exceptions import WorkflowError
import os
import re

# For each snippet, we can optionally define:
# - run script
# - required executor settings for run script
# - setup script
# - required variables for setup script
# - required families (if relevant) to validate

mpi_paths = """
export PATH=/opt/intel/mpi/latest/bin:$PATH
MPI_LD_PATH=/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${MPI_LD_PATH}
"""

mpi_run_script = (
    mpi_paths
    + """
find /opt/intel -name mpicc

# This is important - it won't work without sourcing
source /opt/intel/mpi/latest/env/vars.sh

if [ $BATCH_TASK_INDEX = 0 ]; then
  ls
  which mpirun
  #                                      tasks         tasks per node      # command
  mpirun -hostfile $BATCH_HOSTS_FILE -n %s -ppn %s %s
fi
"""
)

mpi_setup_script = (
    """
sleep $BATCH_TASK_INDEX

# Note that for this family / image, we are root (do not need sudo)
yum update -y && yum install -y cmake gcc tuned ethtool

# This ONLY works on the hpc-* image family images
google_mpi_tuning --nosmt
# google_install_mpi --intel_mpi
google_install_intelmpi --impi_2021
source /opt/intel/mpi/latest/env/vars.sh

# This is where they are installed to
# ls /opt/intel/mpi/latest/
"""
    + mpi_paths
)


class SnippetGroup:
    """
    One or more snippets to add to a setup.
    """

    def __init__(self, spec, settings):
        """
        Snippets must be valid at time of init.
        """
        # Does the snippet group have a run snippet that includes the command?
        self.has_run_command_snippet = False
        self.snippets = []
        self.settings = settings
        self.load(spec)
        self.parse()

    def render_setup(self, command, container):
        """
        Render snippets into a chunk for the setup.
        """
        render = ""
        for snippet in self.snippets:
            render += snippet.render_setup(self.settings, command, container)
        return render

    def render_run(self, command, container):
        """
        Render snippets into a chunk for the run.
        """
        render = ""
        for snippet in self.snippets:
            render += snippet.render_run(self.settings, command, container)
        return render

    def load(self, spec):
        """
        Load a spec for one or more snippets.
        """
        spec = spec or ""
        self.spec = set([x.strip() for x in spec.strip().split(",") if x.strip()])

    def validate(self):
        """
        Validate one or more snippets in a family.
        """
        for snippet in self.snippets:
            # Validate the invidiaul snippet first
            snippet.validate(self.settings)

            # We aren't allowed to have two run snippets wrap the command
            if self.has_run_command_snippet and snippet.includes_command:
                raise WorkflowError(
                    "Only one snippet is allowed to include the command."
                )
            if snippet.includes_command and not self.has_run_command_snippet:
                self.has_run_command_snippet = True

    def parse(self):
        """
        Parse a spec into one or more snippets.
        """
        # Assume they exist (will not validate if not)
        for name in self.spec:
            self.snippets.append(BatchSnippet(name))

    def add(self, snippet):
        """
        Add a snippet to the set.
        """
        self.snippets.append(snippet)


class BatchSnippet:
    """
    A batch snippet goes in the setup step for a Google Batch run.

    There are two types of snippets supported - local files (determined if they exist)
    and named (known) snippets provided here.
    """

    def __init__(self, name):
        self.name = name.strip()
        self.spec = {}
        self.load()

    def is_not_valid(self, reason=""):
        """
        Give a meaningful error message for why not valid.
        """
        msg = f"Snippet {self.name} is not valid"
        raise WorkflowError(f"{msg}: {reason}")

    def validate(self, settings):
        """
        Validate a snippet
        """
        # Family, if defined, must match regular expression
        family = self.spec.get("family")
        if family and not re.search(family, settings.image_family):
            self.is_not_valid(f"Need family {family} but found {settings.image_family}")

    @property
    def includes_command(self):
        """
        Does the snippet include the command (so we should not run it later)?
        """
        return self.spec.get("includes_command", False) or False

    def load(self):
        """
        Load a named snippet.

        We first look to see if it's an existing shell script.
        """
        # A snippet must be known as a built-in name or existing file
        if self.name not in snippets and not os.path.exists(self.name):
            raise WorkflowError(
                f"Snippet {self.name} does not exist as a file and is not known"
            )

        # First preference to files
        if os.path.exists(self.name):
            raise NotImplementedError("Snippets from file are not supported.")
        self.spec = snippets[self.name]


snippets = {
    "intel-mpi": {
        # Regular expression to validate family
        "family": "hpc",
        "setup": mpi_setup_script,
        "run": mpi_run_script,
        # This will mpirun the snakemake command
        "includes_command": True,
    }
}
