# 03 — Daily AWS Cost Alert Using Cost Explorer API and SNS

## Objective
Build an automated daily alert that publishes to SNS (and therefore emails you) when month-to-date AWS spend exceeds a defined threshold.

> **Note:** The legacy CloudWatch "Billing" metric only exists in `us-east-1` and must be manually enabled — it's considered a legacy approach. The modern, interview-relevant approach queries the **Cost Explorer API** (`ce:GetCostAndUsage`) directly, which is what this Lambda does.

## Architecture
```
EventBridge Scheduler (daily)  --->  Lambda (Python 3.12)  --->  Cost Explorer API (ce:GetCostAndUsage)
                                              |
                                              v
                                        SNS Topic ---> Email Subscriber
```

## Prerequisites
- An SNS topic with a confirmed email subscription.
- An IAM role for Lambda with the inline policy in [`iam-inline-policy.json`](./iam-inline-policy.json).
- Cost Explorer enabled on the account (Cost Explorer must be turned on once in the Billing console before `ce:GetCostAndUsage` returns data).

## Step-by-Step Setup

### 1. Create the SNS topic and email subscription
- Create an SNS topic (e.g., `cost-alert-topic`).
- Create a subscription of type **Email**, pointing at your inbox.
- Confirm the subscription via the confirmation email AWS sends.

**Screenshots — SNS topic / subscription / confirmed subscription:**
`screenshots/image14.png`, `screenshots/image15.png`, `screenshots/image16.png`

### 2. Create the Lambda execution role
Attach an inline policy granting:
- `ce:GetCostAndUsage` — read cost data (Cost Explorer actions don't support resource-level scoping, so this is `Resource: "*"`).
- `sns:Publish` — scoped to the specific SNS topic ARN.

See [`iam-inline-policy.json`](./iam-inline-policy.json) — replace `REGION`/`ACCOUNT_ID` with your topic's actual ARN.

**Screenshot — IAM role policy replaced with cost alert ARN:**
`screenshots/image17.png`

### 3. Create the Lambda function
Runtime: **Python 3.12**, handler: `lambda_function.lambda_handler`.

Environment variables required:
| Key | Example value |
|---|---|
| `SNS_TOPIC_ARN` | `arn:aws:sns:ap-south-1:123456789012:cost-alert-topic` |
| `THRESHOLD` | `50` |

Code: [`lambda_function.py`](./lambda_function.py)

Key implementation details:
1. Initializes both a `ce` (Cost Explorer) client and an `sns` client.
2. Builds a month-to-date window: `Start` = first day of current month, `End` = today.
3. Calls `ce.get_cost_and_usage()` with `Granularity='MONTHLY'` and `Metrics=['UnblendedCost']`.
4. Extracts the numeric amount and compares against `THRESHOLD`.
5. If exceeded, publishes a message to the SNS topic with the current spend and threshold.
6. Prints the retrieved amount either way, so CloudWatch Logs always shows the queried cost even when no alert fires.

### 4. Schedule with EventBridge
Create an EventBridge Scheduler rule to invoke the function **daily**.

**Screenshots — EventBridge schedule setup / final schedule:**
`screenshots/image20.png`, `screenshots/image21.png`, `screenshots/image22.png`

### 5. Test
- Temporarily set `THRESHOLD=0.01` in the Lambda environment variables to force an alert regardless of actual spend.
- Manually trigger the function (Test button, empty `{}` event).
- Check CloudWatch Logs for the printed cost and "Alert Sent" message.
- Check your email for the SNS notification.
- Reset `THRESHOLD` back to a realistic value (e.g., `50`) afterward.

**Screenshots — Lambda execution logs / email alert received:**
`screenshots/image18.png`, `screenshots/image19.png`

## Discussion Point: Lambda vs. AWS Budgets
**AWS Budgets** is the managed, no-code alternative for this exact use case — it supports threshold-based email/SNS alerts on cost or usage without writing any Lambda code.

**Use Lambda instead when** you need custom logic AWS Budgets doesn't offer out of the box: per-service or per-tag cost breakdowns in the alert body, delivery to Slack/Microsoft Teams via webhook instead of (or alongside) email, or anomaly-detection-style logic (e.g., "alert only if today's spend is 2x the 7-day average") rather than a flat threshold.

## Files in this folder
| File | Purpose |
|---|---|
| `lambda_function.py` | Lambda handler source code |
| `iam-inline-policy.json` | Inline IAM policy attached to the Lambda execution role |
| `screenshots/` | Console screenshots documenting each step |
