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

For logging, for an interactive run from the command line we provide status updates in the console you have running locally. For full logs, you can
go to the [Google Cloud Batch interface](https://console.cloud.google.com/batch/jobs?project=llnl-flux) and click 
on your job of interest, and then the "Logs" tab. If you don't see logs, look in the "Events" tab, as usually there
is an error with your configuration (e.g., an unknown image or family).

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

### Arguments

And custom arguments can be any of the following, either on the command line or provided in the environment.

| Name | Description | Flag | Type | Environment Variable | Required | Default |
|------|-------------|------|------|----------------------|----------|---------|
| project | The name of the Google Project | `--googlebatch-project` | str | `SNAKEMAKE_GOOGLEBATCH_PROJECT` | True |  unset |
| region | The name of the Google Project region (e.g., us-central1) | str | `--googlebatch-region` |`SNAKEMAKE_GOOGLEBATCH_REGION` | True | unset |
| machine_type | Google Cloud machine type or VM (mpitune configurations are on c2 and c2d family) | str | `--googlebatch-machine-type` | | False | c2-standard-4 |
| image_family | Google Cloud image family (defaults to hpc-centos-7) | `--googlebatch-image-family` | str | | False | hpc-centos-7 |
| image_project | The project the selected image belongs to (defaults to cloud-hpc-image-public) | `--googlebatch-image-project` | str | | False | cloud-hpc-image-public |
| bucket | A bucket to mount with snakemake data | `--googlebatch-bucket` | str | `SNAKEMAKE_GOOGLEBATCH_BUCKET` | True |  unset |
| mount_path | The mount path for a bucket (if provided) | `--googlebatch-mount-path` | str | | False | /mnt/share |
| work_tasks | The default number of work tasks (these are NOT MPI ranks) | `--googlebatch-work-tasks` | int | | False | 1 |
| cpu_milli | Milliseconds per cpu-second | `--googlebatch-cpu-milli` | int | | False | 1000 |
| work_tasks_per_node | The default number of work tasks per node (Google Batch calls these tasks) | `--googlebatch-work-tasks-per-node` | int | | False | 1 |
| memory | Memory in MiB | `--googlebatch-memory` | int | | False | 1000 |
| retry_count | Retry count (default to 1) | `--googlebatch-retry-count` | int | | False | 1 |
| max_run_duration | Maximum run duration, string (e.g., 3600s) | `--googlebatch-max-run-duration` | str | | False | "3600s" |
| labels | Comma separated key value pairs to label job (e.g., model=a3,stage=test) |`--googlebatch-labels` | str | | False | unset|
| container | Container to use (only when image_family is batch-cos*) [see here](https://cloud.google.com/batch/docs/vm-os-environment-overview#supported_vm_os_images) for families/projects | `--googlebatch-container` | str | | False | unset|
| keep_source_cache | Cache workflows in your Google Cloud Storage Bucket | `--googlebatch-keep-source-cache` | bool | | False | False |
| snippet | A comma separated list of one or more snippets to add to your setup | `--googelbatch-snippets` | str | | False | unset |
| preemption-default | Set a default number of preemptible instance retries | `--preemptible-default` | int | False | unset | 
nset |
| preemption-rules | Define custom preemptible instance retries for specific rules | `--preemption-rules` | list | False | unset | 


For machine type, note that for MPI workloads, mpitune configurations are validated on c2 and c2d instances only.
Also note that you can customize the machine type on the level of the step (see [Step Options](#step-options) below).

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