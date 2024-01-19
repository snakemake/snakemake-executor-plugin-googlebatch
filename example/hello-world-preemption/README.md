# Hello World

> with preemtible instances

Here is an example specifying to use an s3 bucket and asking for preemptible instances.

```bash
snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-project llnl-flux --default-storage-provider s3 --default-storage-prefix s3://snakemake-testing-llnl --preemptible-rules
```
