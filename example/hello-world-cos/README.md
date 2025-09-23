# Hello World COS

The example is for the container operating system (COS), which basically means running inside a container
instead of on a native virtual machine. This requires building a custom image. Here is how to see images in
the project:

```bash
gcloud compute images list \
      --project=batch-custom-image \
      --no-standard-images
```

An example rule in snakemake:

```snakemake
rule interpolated_flat_fluvial:
    input:
        interpolated_layers="input.path"
    output:
        touch("output.path")
    resources:
        googlebatch_service_account="svc-acc-name@myproject.iam.gserviceaccount.com",
        googlebatch_image_family="batch-cos-stable-official",
        googlebatch_image_project="batch-custom-image",
        googlebatch_entrypoint="/docker-entrypoint.sh",
        googlebatch_machine_type="e2-standard-4",
        googlebatch_container="europe-docker.pkg.dev/myproject/my_image_name:latest",
        googlebatch_work_tasks=1,
        googlebatch_work_tasks_per_node=2,
    script:
        "relative/path/to/script.py"
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
  --container-image europe-docker.pkg.dev/${GOOGLE_PROJECT}/my_image_name:latest \
  --preemptible-rules name_of_preemptible_rule \
  --default-storage-provider gcs \
  --default-storage-prefix gs://my_bucket_name \
  --verbose \
  my_rule_name
```

See the [Dockerfile](./Dockerfile) and [entrypoint script](./docker-entrypoint.sh) for an example of using micromamba to
build an image with all dependencies installed.

See [this link](https://cloud.google.com/batch/docs/vm-os-environment-overview#supported_vm_os_images) for how to find a
compatible COS image project and family. You can also see
information [here](https://cloud.google.com/batch/docs/view-os-images),