# Hello World (boot disk)

This Snakefile demonstrates how to customize your boot disk.

```bash
$ snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-project llnl-flux --default-storage-provider s3 --default-storage-prefix s3://snakemake-testing-llnl
```