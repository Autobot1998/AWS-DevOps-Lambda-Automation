# 01 — Automated S3 Bucket Cleanup (Objects Older Than 30 Days)

## Objective
Automatically delete stale objects from an S3 bucket using a scheduled AWS Lambda function, instead of manually auditing and cleaning the bucket.

## Architecture
```
EventBridge (schedule, optional)  --->  Lambda (Python 3.12)  --->  S3 Bucket
                                              |
                                              v
                                       CloudWatch Logs
```

## Prerequisites
- An S3 bucket with a mix of old and recent objects.
- An IAM role for Lambda with the inline policy in [`iam-inline-policy.json`](./iam-inline-policy.json).
- Python 3.12+ Lambda runtime (Boto3 is included by default in the Lambda runtime, no layer needed).

## Step-by-Step Setup

### 1. Create the S3 bucket and upload test files
- Create a bucket (example used here: `pravin-cleanup-bucket`).
- Upload several files.
- Since you can't easily backdate an object's `LastModified` timestamp, temporarily lower the age threshold to **minutes** for testing, then switch it back to **30 days** before final submission (see the commented-out testing block in the code).

**Screenshot — bucket contents:**
`screenshots/image1.png`

### 2. Create the Lambda execution role
Create an IAM role for Lambda and attach an **inline policy** scoped to only this bucket:
- `s3:ListBucket` — required to paginate/list objects.
- `s3:DeleteObject` — required to delete stale objects.

See [`iam-inline-policy.json`](./iam-inline-policy.json) for the exact policy document used.

**Screenshots — IAM role permissions / inline policy:**
`screenshots/image2.png`, `screenshots/image3.png`

### 3. Create the Lambda function
Runtime: **Python 3.12**, handler: `lambda_function.lambda_handler`.

Code: [`lambda_function.py`](./lambda_function.py)

Key implementation details:
1. Uses the **paginator** (`s3.get_paginator("list_objects_v2")`) instead of a single `list_objects_v2` call, because S3 only returns up to 1,000 keys per page — a bucket with more objects would silently miss files without pagination.
2. Compares each object's `LastModified` (already timezone-aware, UTC) against `datetime.now(timezone.utc) - timedelta(days=30)`.
3. Deletes any object older than the threshold with `s3.delete_object`.
4. Prints the key of every deleted object for CloudWatch Logs visibility.

### 4. Test
- Temporarily set the threshold to a couple of minutes (see the "Testing" comments in the code) and upload a mix of files, waiting for some to "age past" the threshold.
- Manually trigger the Lambda function (using the **Test** button in the console with an empty `{}` event).
- Confirm in the S3 console that only the newer files remain.
- Set the threshold back to `AGE_THRESHOLD_DAYS = 30` before final submission.

**Screenshots — test input / output / bucket after cleanup:**
`screenshots/image4.png` (test input), `screenshots/image5.png` (test output), `screenshots/image6.png` (bucket state after cleanup)

## Discussion Point: Lambda vs. S3 Lifecycle Rules
**S3 Lifecycle Rules** are the preferred, production-grade solution for simple age-based expiration — they are fully managed by AWS, require zero code, and cost nothing extra to run.

**Use Lambda instead when** deletion depends on logic a Lifecycle Rule can't express — for example: conditional deletion based on object *content* or custom metadata/tags, naming-pattern matching (e.g., delete only `tmp-*` files older than X), or when the deletion needs to trigger a follow-on action in another AWS service (sending a notification, writing an audit record to DynamoDB, invoking another workflow) at the moment of deletion.

## Files in this folder
| File | Purpose |
|---|---|
| `lambda_function.py` | Lambda handler source code |
| `iam-inline-policy.json` | Inline IAM policy attached to the Lambda execution role |
| `screenshots/` | Console screenshots documenting each step |
