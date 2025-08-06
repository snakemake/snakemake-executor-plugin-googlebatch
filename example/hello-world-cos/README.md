# Hello World COS

The example is for the container operating system (COS), which basically means running inside a container
instead of on a native virtual machine. This also means using the default Snakemake image. Here is how to see images in the project:

```bash
gcloud compute images list \
      --project=batch-custom-image \
      --no-standard-images
```

Here is an example command:

```bash
GOOGLE_PROJECT=myproject
snakemake \
  --jobs 1 \
  --executor googlebatch \
  --googlebatch-image-family batch-cos-stable-official \
  --googlebatch-region us-central1 \
  --googlebatch-image-project batch-custom-image \
  --googlebatch-project ${GOOGLE_PROJECT} \
  --default-storage-provider s3 \
  --default-storage-prefix s3://my-snakemake-testing
```

See [this link](https://cloud.google.com/batch/docs/vm-os-environment-overview#supported_vm_os_images) for how to find a compatible COS image project and family.
You can also see information [here](https://cloud.google.com/batch/docs/view-os-images),