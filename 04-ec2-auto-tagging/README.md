# 04 — Auto-Tagging EC2 Instances on Launch

## Objective
Automatically tag every newly launched EC2 instance for resource tracking, ownership, and cost allocation — no manual tagging required.

## Architecture
```
EC2 instance transitions to "running"
        |
        v
EventBridge Rule (source: aws.ec2, detail-type: EC2 Instance State-change Notification, state: running)
        |
        v
Lambda (Python 3.12) --- ec2:CreateTags ---> EC2 instance
        |
        v
CloudWatch Logs
```

## Prerequisites
- An IAM role for Lambda with the inline policy in [`iam-inline-policy.json`](./iam-inline-policy.json).
- Permission to create EventBridge rules.

## Step-by-Step Setup

### 1. Launch a test EC2 instance
Launch (or use an existing) EC2 instance to validate tagging behavior against.

**Screenshot — instance creation:**
`screenshots/image23.png`

### 2. Create the Lambda execution role
Attach an inline policy granting:
- `ec2:CreateTags` — apply tags to the instance.
- `ec2:DescribeInstances` — read instance metadata if needed for conditional tagging logic.

See [`iam-inline-policy.json`](./iam-inline-policy.json).

**Screenshots — IAM role creation / inline policy:**
`screenshots/image24.png`, `screenshots/image25.png`, `screenshots/image26.png`

### 3. Create the Lambda function
Runtime: **Python 3.12**, handler: `lambda_function.lambda_handler`.

Code: [`lambda_function.py`](./lambda_function.py)

Key implementation details:
1. Extracts `instance_id` from `event["detail"]["instance-id"]` — this is the EventBridge event shape for EC2 state-change notifications.
2. Builds a tag set: `LaunchDate` (today's date, UTC), `Environment` (static value, could be parameterized), and `ManagedBy=Lambda`.
3. Calls `ec2.create_tags()` against the instance.
4. Prints a confirmation message to CloudWatch Logs.

### 4. Create the EventBridge rule
Event pattern (see [`eventbridge-rule-pattern.json`](./eventbridge-rule-pattern.json)):
```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": { "state": ["running"] }
}
```
Target: the Lambda function above.

**Screenshots — EventBridge rule / event source configuration:**
`screenshots/image27.png`, `screenshots/image28.png`

### 5. Test
- Launch a new instance (or stop/start an existing one, since a start also fires a "running" state-change event).
- Wait a short delay for the event to propagate through EventBridge.
- Confirm in the EC2 console that the tags (`LaunchDate`, `Environment`, `ManagedBy`) appear on the instance.
- Check CloudWatch Logs to confirm the Lambda executed and printed the confirmation message.

**Screenshots — stopped/started instance for testing, Lambda test confirmation, CloudWatch logs, final tag verification:**
`screenshots/image29.png`, `screenshots/image30.png`, `screenshots/image31.png`, `screenshots/image32.png`

## Bonus: Auto-populate the "Owner" tag from CloudTrail
See [`lambda_function_bonus_cloudtrail_owner.py`](./lambda_function_bonus_cloudtrail_owner.py).

This variant additionally calls `cloudtrail.lookup_events()` filtered to `EventName=RunInstances`, scans the last 15 minutes of management events, and matches the `instance_id` inside the raw CloudTrail event JSON to identify the IAM user or role (`Username` field) that launched the instance. That identity is then added as an `Owner` tag alongside the standard tags.

This requires one additional IAM permission on the Lambda role:
```json
{
  "Sid": "ReadCloudTrailHistory",
  "Effect": "Allow",
  "Action": "cloudtrail:LookupEvents",
  "Resource": "*"
}
```

**Practical caveat:** CloudTrail events can take a few minutes to become searchable via `lookup_events`, so in a production setup this owner-tagging step is often better handled by a second, slightly-delayed Lambda invocation (e.g., re-triggered a few minutes later) rather than assuming the CloudTrail event is already queryable at the exact moment the instance reaches "running" state.

## Files in this folder
| File | Purpose |
|---|---|
| `lambda_function.py` | Base Lambda handler (LaunchDate/Environment/ManagedBy tags) |
| `lambda_function_bonus_cloudtrail_owner.py` | Extended handler that also adds an `Owner` tag via CloudTrail lookup |
| `iam-inline-policy.json` | Inline IAM policy attached to the Lambda execution role |
| `eventbridge-rule-pattern.json` | EventBridge rule event pattern |
| `screenshots/` | Console screenshots documenting each step |
