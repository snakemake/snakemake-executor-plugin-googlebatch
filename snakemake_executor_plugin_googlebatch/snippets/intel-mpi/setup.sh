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
{% include "intel-mpi/include/paths.sh" %}
