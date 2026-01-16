### Setup

You'll likely want to start by setting up [application default credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to)
The easiest thing to do is run:

```bash
gcloud auth application-default login
```

### Quick Start

The basic usage is, from a directory with your Snakefile, to ask for `googlebatch` as the
executor.

```bash
$ snakemake --jobs 1 --executor googlebatch
```

You are minimally required to provide a project and region, and can do this through the environment or command line:

```bash
export SNAKEMAKE_GOOGLEBATCH_PROJECT=myproject
export SNAKEMAKE_GOOGLEBATCH_REGION=us-central1
snakemake --jobs 1 --executor googlebatch
```

or

```bash
export SNAKEMAKE_GOOGLEBATCH_PROJECT=myproject
export SNAKEMAKE_GOOGLEBATCH_REGION=us-central1
snakemake --jobs 1 --executor googlebatch --googlebatch-project myproject --googlebatch-region us-central1
```

You can provide one or more custom arguments, as shown in the table below, to customize your batch run.
Note that batch offers setup snippets to help with more complex setups (e.g,. MPI). See [batch snippets](#batch-snippets)
for more information.


### Logging

For logging, for an interactive run from the command line we provide status updates in the console you have running locally.
For full logs, you can go to the [Google Cloud Batch interface](https://console.cloud.google.com/batch/jobs) and click 
on your job of interest, and then the "Logs" tab. If you don't see logs, look in the "Events" tab, as usually there is an error with your configuration (e.g., an unknown image or family).
It is important to [enable the logging API](https://cloud.google.com/logging/docs/api/enable-api) for this to work.

#### Isolated Logs

If you need to retrieve logs for a job outside of this context (e.g., after a run or in a Pythonic test) you can use the provided script in [example](example).
Here is how to run it using the local poetry environment. You can either provide `--project` and `--region` or export the environment variables for them
described above.

```bash
#                                       <jobid>
poetry run python example/show-logs.py a-898674
```

Note that this is currently provided as a helper script because the [Google Cloud API limits](https://cloud.google.com/logging/quotas#api-limits)
set a rate limit of 60/minute. 

> Number of entries.list requests 60 per minute, per Google Cloud project

For some perspective, a "hello world" job will produce over 3K lines of logs, and (without a sleep between calls)
the ratelimit is hit very easily. We are currently assessing strategies to deliver full logs to .snakemake logging files
without hitting issues with this rate limit. It looks possible to create "[sinks](https://cloud.google.com/logging/docs/routing/overview#sinks)" using
Pub Sub, however this would be adding an extra API dependency (and cost). 

#### Choosing an Image

You can read about how to choose an image [here](https://cloud.google.com/batch/docs/view-os-images). Note that
the image family and project must match or you'll see that your job does not run (but has an event that indicates a mismatch in the online table).
Since this is a changing set we do not validate, however we suggest that you check before running to not waste time.
I am not entirely sure how to choose correctly, because there is some information [here]() but this listing offers
different information:

```bash
gcloud compute images list | grep cos
```

### Batch Snippets

Batch, by way of running on virtual machines, can support custom more complex setups or running steps such as running MPI.
However, the setups here are non trivial, so if you choose, a custom snippet can be added. There are
two types of snippets:

 - named, built-in snippets provided by the googlebatch executor plugin here
 - your custom snippet provided via a script file (not implemented yet)

For each named snippet, depending on the functionality it might add custom logic to the setup or final runnable step.
Examples for providing both are shown below. To determine if the snippet is custom, it should be a json or yaml file that
exists. The order that you provide any number of snippets is the order they
are added. To provide more than one, provide them via a comma separated list.

```bash
$ snakemake --jobs 1 --executor googlebatch --googlebatch-bucket snakemake-cache-dinosaur --googlebatch-snippets intel-mpi
```

### Additional Environment Variables

The following environment variables are available within any Google batch run:

 - `BATCH_TASK_INDEX`: The index of the workflow step (Google Batch calls a "task")
 - `GOOGLEBATCH_DOCKER_PASSWORD`: your docker registry passwork if using the container operating system (COS) and your container requires credentials
 - `GOOGLEBATCH_DOCKER_USERNAME`: the same, but the username

### GPU

The Google Batch executor uses the same designation for GPUs as core Snakemake. However, you should 
[keep compatibility of machine type](https://cloud.google.com/compute/docs/gpus) with the GPU
that you selected in mind. For example, if you select `nvidia_gpu=1` you will need an n1-* family machine type.

On a n1-* family machine type, nvidia_gpu=1 will trigger a "nvidia-tesla-t4" gpu by default.

It's possible to change the gpu type directly using a machine-compatible label:
e.g. nvidia_gpu='nvidia-tesla-v100'

### Step Options

The following options are allowed for batch steps. This predominantly includes most arguments.

#### googlebatch_machine_type

This will define the machine type for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_machine_type="c3-standard-112"
    shell:
        "..."
```

Note that for MPI workloads, mpitune configurations are validated on c2 and c2d instances only.


#### googlebatch_image_family

This will define the image family for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_image_family="hpc-centos-7"
    shell:
        "..."
```

Note that the way to get updated names is to run:

```bash
gcloud compute images list \
    --project=batch-custom-image \
    --no-standard-images
```

And see [this page](https://cloud.google.com/batch/docs/view-os-images) for more details.

#### googlebatch_image_project

This will define the image project for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_image_project="cloud-hpc-image-public"
    shell:
        "..."
```


#### googlebatch_bucket

This will define the bucket for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_bucket="my-snakemake-batch-bucket"
    shell:
        "..."
```

#### googlebatch_mount_path

This will define the mount path for a bucket for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_mount_path="/mnt/workflow"
    shell:
        "..."
```


#### googlebatch_work_tasks

This will define the work tasks for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_work_tasks=1
    shell:
        "..."
```

#### googlebatch_network

The URL of an existing network resource (e.g., `projects/{project}/global/networks/{network}`)

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_network="projects/{project}/global/networks/{network}"
    shell:
        "..."
```

#### googlebatch_subnetwork

The URL of an existing subnetwork resource (e.g., `projects/{project}/regions/{region}/subnetworks/{subnetwork}`)

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_subnetwork="projects/{project}/regions/{region}/subnetworks/{subnetwork}"
    shell:
        "..."
```

#### googlebatch_service_account

The email of custom compute service account to be used by Batch (e.g., `snakemake-sa@projectid.iam.gserviceaccount.com`)

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_service_account="snakemake-sa@projectid.iam.gserviceaccount.com"
    shell:
        "..."
```

#### googlebatch_cpu_milli

This will define the milliseconds per cpu-second for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_cpu_mulli=2000
    shell:
        "..."
```

#### googlebatch_work_tasks_per_node

This will define the work tasks per node (Google batch calls these tasks) for a particular step, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_work_tasks_per_node=2
    shell:
        "..."
```

#### googlebatch_memory

This will define the memory for a particular step as an integer in MiB, overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_memory=2000
    shell:
        "..."
```


#### googlebatch_boot_disk_type

This is the [boot disk type](https://cloud.google.com/compute/docs/disks#pdspecs).

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_boot_disk_type="pd-standard"
    shell:
        "..."
```


#### googlebatch_boot_disk_image

This is the boot disk [image](https://github.com/googleapis/googleapis/blob/2fd7625cf9808234503fd5addc6e2bda8fe5c114/google/cloud/batch/v1/job.proto#L287-L292). If not set, we use the family defined for the job.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_boot_disk_image="batch-centos"
    shell:
        "..."
```


#### googlebatch_boot_disk_gb

The [size of the boot disk](https://github.com/googleapis/googleapis/blob/2fd7625cf9808234503fd5addc6e2bda8fe5c114/google/cloud/batch/v1/job.proto#L314-L324) in GB. This needs to be 30 (default) or larger

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_boot_disk_gb=40
    shell:
        "..."
```

#### googlebatch_retry_count

This will define the retry times for a step overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_retry_count=2
    shell:
        "..."
```

#### googlebatch_max_run_duration

This will define the max run duration for a step overriding the default from the command line.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_max_run_duration="3600s"
    shell:
        "..."
```

#### googlebatch_labels

This will define the extra labels to add to the Google Batch job.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_labels="model=c3,stage=test"
    shell:
        "..."
```


#### googlebatch_container

A container to use only with `image_family` set to batch-cos* (see [here](https://cloud.google.com/batch/docs/vm-os-environment-overview#supported_vm_os_images) for how to see VM choices)

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_container="ghcr.io/rse-ops/atacseq:app-latest"
    shell:
        "..."
```


#### googlebatch_snippets

One or more named (or file-derived) snippets to add to setup.

```console
rule hello_world:
    output:
        "...",
    resources: 
        googlebatch_snippets="mpi,myscript.sh"
    shell:
        "..."
```
