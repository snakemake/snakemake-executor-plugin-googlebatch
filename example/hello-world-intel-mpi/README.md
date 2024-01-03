# Hello World Intel MPI

This example shows requesting using the intel MPI snippet, which means adding a custom setup and run
command to your code. An hpc-* flavored family is required (which is the default).

```bash
GOOGLE_PROJECT=myproject
snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-project ${GOOGLE_PROJECT} --default-storage-provider s3 --default-storage-prefix s3://my-snakemake-testing --googlebatch-snippets intel-mpi
```

Note that the workflow functions, but the output file is empty, and we believe this to be a bug with the original workflow.
An issue has been [opened here](https://github.com/snakemake/snakemake-executor-plugin-googlebatch/issues/18).