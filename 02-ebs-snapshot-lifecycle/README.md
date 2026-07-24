# 02 — Automated EBS Snapshot Creation and Cleanup

## Objective
Automate weekly EBS volume backups (snapshots) and clean up snapshots older than a retention period, using a scheduled Lambda function.

## Architecture
```
EventBridge Scheduler (weekly)  --->  Lambda (Python 3.12)  --->  EC2 / EBS Snapshots
                                              |
                                              v
                                       CloudWatch Logs
```

## Prerequisites
- An existing EBS volume (or one created for this exercise) — note its Volume ID.
- An IAM role for Lambda with the inline policy in [`iam-inline-policy.json`](./iam-inline-policy.json).

## Step-by-Step Setup

### 1. Identify the EBS volume
Locate (or create) an EBS volume in the EC2 console and note its Volume ID — used here: `vol-0acac002c72ed866a`.

**Screenshot — EBS volume:**
`screenshots/image7.png`

### 2. Create the Lambda execution role
Attach an inline policy granting:
- `ec2:CreateSnapshot` — create the backup.
- `ec2:DescribeSnapshots` — list existing snapshots to evaluate age.
- `ec2:DeleteSnapshot` — remove snapshots past retention.
- `ec2:CreateTags` — tag the snapshot so it can be identified later.

See [`iam-inline-policy.json`](./iam-inline-policy.json).

**Screenshots — IAM role / inline policy:**
`screenshots/image8.png`, `screenshots/image9.png`

### 3. Create the Lambda function
Runtime: **Python 3.12**, handler: `lambda_function.lambda_handler`.

Code: [`lambda_function.py`](./lambda_function.py)

Key implementation details:
1. Calls `ec2.create_snapshot()` against the hardcoded `VOLUME_ID`.
2. Immediately tags the new snapshot with `CreatedBy=Lambda-Backup`, so subsequent runs can filter for only the snapshots this function manages (as opposed to manual or console-created snapshots).
3. Calls `ec2.describe_snapshots()` scoped to `OwnerIds=["self"]` and filtered by the `CreatedBy` tag.
4. Compares each returned snapshot's `StartTime` against a 30-day cutoff and deletes anything older.
5. Prints the created snapshot ID and every deleted snapshot ID for CloudWatch Logs visibility.

### 4. Schedule with EventBridge
Create an EventBridge Scheduler rule to run this function **weekly** (e.g., `rate(7 days)` or a `cron` expression).

**Screenshots — EventBridge scheduler setup / final schedule:**
`screenshots/image11.png`, `screenshots/image12.png`, `screenshots/image13.png`

### 5. Test
- Manually invoke the Lambda (Test button, empty `{}` event).
- Confirm a new snapshot appears in the EC2 → Snapshots console, tagged `CreatedBy=Lambda-Backup`.
- Confirm old snapshots (if any exist past the retention window) are removed.

**Screenshot — snapshot deleted / cleaned up:**
`screenshots/image10.png`

## Discussion Point: Lambda vs. AWS Data Lifecycle Manager (DLM)
**AWS Data Lifecycle Manager (DLM)** is the AWS-native, managed solution for routine EBS snapshot creation and retention — it requires no code and handles standard "snapshot every N days, keep M copies" policies out of the box.

**Use Lambda instead when** you need logic DLM doesn't support: retention periods that vary by tag/environment (e.g., prod = 90 days, dev = 7 days), copying snapshots cross-account or cross-region as part of a DR strategy, gating snapshot deletion behind an approval workflow, or sending custom notifications (SNS/Slack/Teams) when backups succeed or fail.

## Files in this folder
| File | Purpose |
|---|---|
| `lambda_function.py` | Lambda handler source code |
| `iam-inline-policy.json` | Inline IAM policy attached to the Lambda execution role |
| `screenshots/` | Console screenshots documenting each step |
