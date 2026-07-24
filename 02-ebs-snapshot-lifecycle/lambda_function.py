"""
Automated EBS Snapshot Creation and Cleanup

Creates a new snapshot of a specified EBS volume, tags it, then scans
all snapshots owned by this account carrying the same tag and deletes
any older than the retention period. Intended to run on a weekly
EventBridge schedule.
"""

import boto3
from datetime import datetime, timezone, timedelta

ec2 = boto3.client("ec2")

VOLUME_ID = "vol-0acac002c72ed866a"
RETENTION_DAYS = 30


def lambda_handler(event, context):
    # 1. Create a new snapshot of the target volume
    response = ec2.create_snapshot(
        VolumeId=VOLUME_ID,
        Description="Automated Lambda Backup"
    )
    snapshot_id = response["SnapshotId"]

    # 2. Tag the new snapshot so we can identify "our" snapshots later
    ec2.create_tags(
        Resources=[snapshot_id],
        Tags=[
            {
                "Key": "CreatedBy",
                "Value": "Lambda-Backup"
            }
        ]
    )
    print(f"Created Snapshot: {snapshot_id}")

    # 3. Find and delete snapshots older than the retention period
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

    snapshots = ec2.describe_snapshots(
        OwnerIds=["self"],
        Filters=[
            {
                "Name": "tag:CreatedBy",
                "Values": ["Lambda-Backup"]
            }
        ]
    )

    deleted = []
    for snapshot in snapshots["Snapshots"]:
        if snapshot["StartTime"] < cutoff:
            ec2.delete_snapshot(SnapshotId=snapshot["SnapshotId"])
            deleted.append(snapshot["SnapshotId"])
            print(f"Deleted Snapshot: {snapshot['SnapshotId']}")

    return {
        "CreatedSnapshot": snapshot_id,
        "DeletedSnapshots": deleted
    }
