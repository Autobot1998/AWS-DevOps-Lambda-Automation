"""
Auto-Tagging EC2 Instances on Launch

Triggered by an EventBridge rule that matches EC2 "running" state-change
notifications. Tags the newly running instance with a launch date and
ownership/environment metadata for cost allocation and tracking.
"""

import boto3
from datetime import datetime

ec2 = boto3.client("ec2")


def lambda_handler(event, context):
    print("Received Event:")
    print(event)

    instance_id = event["detail"]["instance-id"]
    launch_date = datetime.utcnow().strftime("%Y-%m-%d")

    tags = [
        {
            "Key": "LaunchDate",
            "Value": launch_date
        },
        {
            "Key": "Environment",
            "Value": "Development"
        },
        {
            "Key": "ManagedBy",
            "Value": "Lambda"
        }
    ]

    ec2.create_tags(
        Resources=[instance_id],
        Tags=tags
    )

    print(f"Successfully tagged {instance_id}")

    return {
        "statusCode": 200,
        "instance": instance_id
    }
