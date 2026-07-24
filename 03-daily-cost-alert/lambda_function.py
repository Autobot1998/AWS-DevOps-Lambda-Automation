"""
Daily AWS Cost Alert Using Cost Explorer API and SNS

Queries month-to-date UnblendedCost via the Cost Explorer API and
publishes an SNS notification if spend exceeds a configured threshold.
Intended to run daily via EventBridge.
"""

import boto3
import os
from datetime import datetime

ce = boto3.client('ce')
sns = boto3.client('sns')

SNS_TOPIC = os.environ["SNS_TOPIC_ARN"]
THRESHOLD = float(os.environ["THRESHOLD"])


def lambda_handler(event, context):
    today = datetime.utcnow().date()
    start = today.replace(day=1).strftime('%Y-%m-%d')
    end = today.strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start,
            'End': end
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    amount = float(
        response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
    )

    print(f"Current Month Cost: ${amount:.2f}")

    if amount > THRESHOLD:
        message = (
            f"AWS spending exceeded threshold!\n\n"
            f"Current Spend: ${amount:.2f}\n"
            f"Threshold: ${THRESHOLD:.2f}"
        )
        sns.publish(
            TopicArn=SNS_TOPIC,
            Subject="AWS Cost Alert",
            Message=message
        )
        print("Alert Sent")
    else:
        print("Threshold Not Reached")

    return {
        "CurrentCost": amount
    }
