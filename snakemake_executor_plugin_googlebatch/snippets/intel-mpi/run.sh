{% include "intel-mpi/include/paths.sh" %}

find /opt/intel -name mpicc

# This is important - it won't work without sourcing
source /opt/intel/mpi/latest/env/vars.sh

if [ $BATCH_TASK_INDEX = 0 ]; then
  ls
  which mpirun
  echo "{% if resources.mpi %}{{ resources.mpi }}{% else %}mpiexec{% endif %} -hostfile $BATCH_HOSTS_FILE -n {{ settings.tasks }} -ppn {{ settings.tasks_per_node }} {{ command }}"
  {% if resources.mpi %}{{ resources.mpi }}{% else %}mpiexec{% endif %} -hostfile $BATCH_HOSTS_FILE -n {{ settings.tasks }} -ppn {{ settings.tasks_per_node }} {{ command }}
fi
