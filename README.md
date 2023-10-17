# Snakemake Executor Google Batch

> This is currently a skeleton and not ready for use, but come back soon! 🎃️

This is the [Google Batch](https://cloud.google.com/batch/docs/get-started) external executor plugin for snakemake.
If you are migrating from Google Life Sciences see [this documentation](https://cloud.google.com/batch/docs/migrate-to-batch-from-cloud-life-sciences). For the underlying Python SDK, see [google-cloud-batch](https://github.com/googleapis/google-cloud-python/tree/main/packages/google-cloud-batch) on GitHub.


## Usage

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

### Arguments

And custom arguments can be any of the following, either on the command line or provided in the environment.

| Name | Description | Flag | Type | Environment Variable | Required | Default |
|------|-------------|------|------|----------------------|----------|---------|
| project | The name of the Google Project | `--googlebatch-project` | str | `SNAKEMAKE_GOOGLEBATCH_PROJECT` | True |  unset |
| region | The name of the Google Project region (e.g., us-central1) | str | `--googlebatch-region` |`SNAKEMAKE_GOOGLEBATCH_REGION` | True | unset |
| machine_type | Google Cloud machine type or VM (mpitune configurations are on c2 and c2d family) | str | `--googlebatch-machine-type` | | False | c2-standard-4 |
| image_family | Google Cloud image family (defaults to hpc-centos-7) | str | `--googlebatch-image-family` | | False | hpc-centos-7 |
| image_project | The project the selected image belongs to (defaults to cloud-hpc-image-public) | str |  `--googlebatch-image-project` | | False | cloud-hpc-image-public |
| bucket | A bucket to mount with snakemake data | str | `--googlebatch-bucket` | | False |  unset |
| mount_path | The mount path for a bucket (if provided) | str | `--googlebatch-mount-path` | | False | /mnt/share |
| work_tasks | The default number of work tasks (these are NOT MPI ranks) | int | `--googlebatch-work-tasks` | | False | 1 |
| cpu_milli | Milliseconds per cpu-second | int| `--googlebatch-cpu-milli` | | False | 1000 |
| work_tasks_per_node | The default number of work tasks per node (Google Batch calls these tasks) | int | `--googlebatch-work-tasks-per-node` | | False | 1 |
| memory | Memory in MiB | int | `--googlebatch-memory` | | False | 1000 |
| retry_count | Retry count (default to 1) | int | `--googlebatch-retry-count` | | False | 1 |
| max_run_duration | Maximum run duration, string (e.g., 3600s) | str | `--googlebatch-max-run-duration` | | False | "3600s" |
| labels | Comma separated key value pairs to label job (e.g., model=a3,stage=test) | str | `--googlebatch-labels` | | False | unset|
For machine type, note that for MPI workloads, mpitune configurations are validated on c2 and c2d instances only.
Also note that you can customize the machine type on the level of the step (see [Step Options](#step-options) below).

### Additional Environment Variables

The following environment variables are available within any Google batch run:

 - `BATCH_TASK_INDEX`: The index of the workflow step (Google Batch calls a "task")

### Step Options

The following options are allowed for batch steps. This predominantly includes most arguments.

#### googlebatch_machine_type

This will define the machine type for a particular step, overriding the default from the command line.

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
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

```yaml
rule hello_world:
	output:
		"...",
	resources: 
		googlebatch_labels="model=c3,stage=test"
	shell:
        "..."
```

### Questions

- What leads to STATE_UNSPECIFIED?
- Should MPI barriers / install be integrated into wrappers or here?
- How do we represent more than one runnable in a step?
- How do we install Snakemake without a container?

### Tutorial

For this tutorial, we will start int he Example directory.

```bash
$ cd ./example

# This says "use the custom executor module named snakemake_executor_plugin_googlebatch"
$ snakemake --jobs 1 --executor googlebatch
```

```console
Building DAG of jobs...
Using shell: /bin/bash
Job stats:
job                         count    min threads    max threads
------------------------  -------  -------------  -------------
all                             1              1              1
multilingual_hello_world        2              1              1
total                           3              1              1

Select jobs to execute...

[Fri Jun 16 19:24:22 2023]
rule multilingual_hello_world:
    output: hola/world.txt
    jobid: 2
    reason: Missing output files: hola/world.txt
    wildcards: greeting=hola
    resources: tmpdir=/tmp

Job 2 has been submitted with flux jobid ƒcjn4t3R (log: .snakemake/flux_logs/multilingual_hello_world/greeting_hola.log).
[Fri Jun 16 19:24:32 2023]
Finished job 2.
1 of 3 steps (33%) done
Select jobs to execute...

[Fri Jun 16 19:24:32 2023]
rule multilingual_hello_world:
    output: hello/world.txt
    jobid: 1
    reason: Missing output files: hello/world.txt
    wildcards: greeting=hello
    resources: tmpdir=/tmp

Job 1 has been submitted with flux jobid ƒhAPLa79 (log: .snakemake/flux_logs/multilingual_hello_world/greeting_hello.log).
[Fri Jun 16 19:24:42 2023]
Finished job 1.
2 of 3 steps (67%) done
Select jobs to execute...

[Fri Jun 16 19:24:42 2023]
localrule all:
    input: hello/world.txt, hola/world.txt
    jobid: 0
    reason: Input files updated by another job: hello/world.txt, hola/world.txt
    resources: tmpdir=/tmp

[Fri Jun 16 19:24:42 2023]
Finished job 0.
3 of 3 steps (100%) done
Complete log: .snakemake/log/2023-06-16T192422.186675.snakemake.log
```

And that's it! Continue reading to learn more about plugin design, and how you can also design your own executor
plugin for use or development (that doesn't need to be added to upstream snakemake).

## Developer

The instructions for creating and scaffolding this plugin are [here](https://github.com/snakemake/poetry-snakemake-plugin#scaffolding-an-executor-plugin).
Instructions for writing your plugin with examples are provided via the [snakemake-executor-plugin-interface](https://github.com/snakemake/snakemake-executor-plugin-interface).
