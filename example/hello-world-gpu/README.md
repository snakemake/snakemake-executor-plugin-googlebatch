# Hello World + GPU

Here is an example that runs hello world, but asks for a GPU resource.

```bash
$ snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-machine-type n1-standard-8 --googlebatch-project llnl-flux --default-storage-provider s3 --default-storage-prefix s3://snakemake-testing-llnl
```
