# Hello World Intel MPI

This example shows requesting using the intel MPI snippet, which means adding a custom setup and run
command to your code. An hpc-* flavored family is required (which is the default).

```bash
snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-project llnl-flux --default-storage-provider s3 --default-storage-prefix s3://snakemake-testing-llnl --googlebatch-snippets intel-mpi
```

