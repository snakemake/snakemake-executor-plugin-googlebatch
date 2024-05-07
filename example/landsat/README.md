# Landsat Example

Here is an example specifying to use an s3 bucket

```bash
snakemake --jobs 1 --executor googlebatch --googlebatch-region us-central1 --googlebatch-project llnl-flux --default-storage-provider gcs --default-storage-prefix gcs://change-me --storage-gcs-project llnl-flux
```
