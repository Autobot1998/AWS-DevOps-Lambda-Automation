"""
Bonus: Auto-Tagging EC2 Instances on Launch + Owner Tag from CloudTrail

Extends the base auto-tagging function by looking up the IAM identity
that launched the instance via CloudTrail's RunInstances event, and
adds that identity as an "Owner" tag. This is a common interview
follow-up question for this exercise.

Notes:
- CloudTrail events can take a few minutes to become queryable, so in
  practice this lookup is best done by a second, delayed Lambda
  (e.g., triggered a few minutes later, or on a short EventBridge
  schedule) rather than the same instant the "running" event fires.
- lookup_events is rate-limited and only searches the last 90 days of
  management events by default (or a custom trail's event history).
"""

import boto3
from datetime import datetime, timedelta

ec2 = boto3.client("ec2")
cloudtrail = boto3.client("cloudtrail")


def get_launching_user(instance_id):
    """Search CloudTrail for the RunInstances event tied to this instance
    and return the identity (IAM user/role ARN) that made the call."""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)

    response = cloudtrail.lookup_events(
        LookupAttributes=[
            {
                "AttributeKey": "EventName",
                "AttributeValue": "RunInstances"
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        MaxResults=50
    )

    for event in response.get("Events", []):
        cloudtrail_event = event.get("CloudTrailEvent", "")
        if instance_id in cloudtrail_event:
            username = event.get("Username", "unknown")
            return username

    return "unknown"


def lambda_handler(event, context):
    print("Received Event:")
    print(event)

    instance_id = event["detail"]["instance-id"]
    launch_date = datetime.utcnow().strftime("%Y-%m-%d")
    owner = get_launching_user(instance_id)

    tags = [
        {"Key": "LaunchDate", "Value": launch_date},
        {"Key": "Environment", "Value": "Development"},
        {"Key": "ManagedBy", "Value": "Lambda"},
        {"Key": "Owner", "Value": owner}
    ]

    ec2.create_tags(
        Resources=[instance_id],
        Tags=tags
    )

    print(f"Successfully tagged {instance_id} with Owner={owner}")

    return {
        "statusCode": 200,
        "instance": instance_id,
        "owner": owner
    }
