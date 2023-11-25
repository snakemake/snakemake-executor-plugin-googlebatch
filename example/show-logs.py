#!/usr/bin/env python3

# A helper script to show snakemake logs in real time.
# https://cloud.google.com/batch/docs/analyze-job-using-logs#python
# usage:
#         python show-logs.py <jobid>

from __future__ import annotations

import argparse
import time
import os
import sys

from google.cloud import batch_v1, logging


def get_parser():
    parser = argparse.ArgumentParser(
        description="Snakemake Google Batch Logs Streamer",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "jobid",
        help="job id to steam logs for",
    )
    parser.add_argument(
        "--project",
        help="Google Project (can also be provided with SNAKEMAKE_GOOGLEBATCH_PROJECT in environment",
    )
    parser.add_argument(
        "--region",
        help="Google region (defaults to us-central1)",
        default="us-central1",
    )
    parser.add_argument(
        "--sleep",
        help="Sleep seconds between log line requests (defaults to 1.1 seconds)",
        default=1.1,
        type=float,
    )
    return parser


def main():
    """
    Show logs for a job id.
    """
    parser = get_parser()
    args, _ = parser.parse_known_args()

    project = args.project or os.environ.get("SNAKEMAKE_GOOGLEBATCH_PROJECT")
    region = args.region or os.environ.get("SNAKEMAKE_GOOGLEBATCH_REGION")

    if not project:
        sys.exit(
            "Please provide your Google project with --project or in the environment."
        )
    if not args.jobid:
        sys.exit("A job id is required as the only positional argument.")

    print(f"🌟️ Project: {project}")
    print(f"🌟️ Region: {region}")
    print(f"🌟️ Sleep: {args.sleep} seconds")

    # Create a client to get the job
    client = batch_v1.BatchServiceClient()
    name = f"projects/{project}/locations/{region}/jobs/{args.jobid}"
    try:
        job = client.get_job(name=name)
    except Exception as e:
        sys.exit(f"Cannot get job {name}: {e}")

    # Initialize client that will be used to send requests across threads. This
    # client only needs to be created once, and can be reused for multiple requests.
    log_client = logging.Client(project=project)
    logger = log_client.logger("batch_task_logs")
    for log_entry in logger.list_entries(filter_=f"labels.job_uid={job.uid}"):
        # Note that without the sleep you will exceed the wait limit
        # 60/minute, so we break with added buffer
        time.sleep(args.sleep)
        print(log_entry.payload)


if __name__ == "__main__":
    main()
