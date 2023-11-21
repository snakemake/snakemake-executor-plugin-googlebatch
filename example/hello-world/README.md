# Hello World

Note that `--googlebatch-bucket` is required as a bucket to put workflow cache assets under "cache" 
If it does not exist it will be created.

This prefix we will delete later
```bash
prefix="s3://snakemake-test-googlebatch"
```

```bash
# This says "use the custom executor module named snakemake_executor_plugin_googlebatch"
$ snakemake --jobs 1 --executor googlebatch --googlebatch-bucket snakemake-cache-dinosaur --googlebatch-region us-central1 --googlebatch-project llnl-flux --default-storage-provider s3 --default-storage-prefix $prefix --storage-s3-endpoint-url https://play.minio.io:9000 --storage-s3-access-key Q3AM3UQ867SPQQA43P2F --storage-s3-secret-key zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG 
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
