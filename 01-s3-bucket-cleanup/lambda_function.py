"""
Automated S3 Bucket Cleanup (Objects Older Than 30 Days)

Deletes objects in a specified S3 bucket whose LastModified timestamp
is older than a configurable age threshold. Designed to run on a
manual trigger or an EventBridge schedule (e.g., daily).
"""

import boto3
from datetime import datetime, timezone, timedelta

# ---------------------------------------------
# Configuration
# ---------------------------------------------
BUCKET_NAME = "pravin-cleanup-bucket"

# Production threshold
AGE_THRESHOLD_DAYS = 30

# Testing threshold (uncomment to test with a short window instead of 30 days)
# AGE_THRESHOLD_MINUTES = 2

s3 = boto3.client("s3")


def lambda_handler(event, context):
    deleted_files = []

    # Production cutoff
    threshold_time = datetime.now(timezone.utc) - timedelta(days=AGE_THRESHOLD_DAYS)

    # Testing cutoff (swap the line above for this one, then set back before final submission)
    # threshold_time = datetime.now(timezone.utc) - timedelta(minutes=AGE_THRESHOLD_MINUTES)

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME)

    for page in pages:
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            key = obj["Key"]
            last_modified = obj["LastModified"]  # already timezone-aware (UTC)

            if last_modified < threshold_time:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                deleted_files.append(key)
                print(f"Deleted: {key}")

    return {
        "statusCode": 200,
        "deleted_files": deleted_files
    }
