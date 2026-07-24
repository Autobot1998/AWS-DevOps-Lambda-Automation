# AWS DevOps Automation Labs

A collection of four self-contained AWS Lambda automation exercises built as part of a DevOps/Cloud Computing program. Each exercise covers a common operational automation pattern using Python 3.12 + Boto3, IAM least-privilege inline policies, and EventBridge scheduling/event triggers.

## Repository Structure
```
aws-devops-automation-labs/
├── README.md                            <- you are here
├── 01-s3-bucket-cleanup/
│   ├── README.md
│   ├── lambda_function.py
│   ├── iam-inline-policy.json
│   └── screenshots/
├── 02-ebs-snapshot-lifecycle/
│   ├── README.md
│   ├── lambda_function.py
│   ├── iam-inline-policy.json
│   └── screenshots/
├── 03-daily-cost-alert/
│   ├── README.md
│   ├── lambda_function.py
│   ├── iam-inline-policy.json
│   └── screenshots/
└── 04-ec2-auto-tagging/
    ├── README.md
    ├── lambda_function.py
    ├── lambda_function_bonus_cloudtrail_owner.py
    ├── iam-inline-policy.json
    ├── eventbridge-rule-pattern.json
    └── screenshots/
```

Each folder is independent — its own Lambda source, its own scoped IAM inline policy, its own README with full setup/test/discussion notes, and its own screenshot evidence from the console.

## Exercises

| # | Folder | Summary | Trigger |
|---|---|---|---|
| 1 | [`01-s3-bucket-cleanup`](./01-s3-bucket-cleanup) | Deletes S3 objects older than 30 days | Manual / schedule |
| 2 | [`02-ebs-snapshot-lifecycle`](./02-ebs-snapshot-lifecycle) | Creates + tags EBS snapshots, deletes ones past retention | EventBridge (weekly) |
| 3 | [`03-daily-cost-alert`](./03-daily-cost-alert) | Checks month-to-date AWS spend via Cost Explorer, alerts via SNS | EventBridge (daily) |
| 4 | [`04-ec2-auto-tagging`](./04-ec2-auto-tagging) | Auto-tags EC2 instances on launch (+ bonus CloudTrail owner lookup) | EventBridge (EC2 state-change event) |

## Common Conventions Across All Exercises
- **Runtime:** Python 3.12, `boto3` (bundled with the Lambda runtime — no layer needed).
- **IAM:** every Lambda execution role uses a scoped **inline policy** (not a managed policy) granting only the specific actions each function needs, plus the standard CloudWatch Logs permissions.
- **Testing pattern:** each function is first manually invoked via the Lambda console **Test** feature with an empty `{}` event (except #4, which is driven by a real EC2 state-change event), then verified against the relevant AWS console (S3, EC2, SNS/email, CloudWatch Logs).
- **Discussion point:** each README closes with a short comparison against the equivalent AWS-managed/no-code service (S3 Lifecycle Rules, AWS Data Lifecycle Manager, AWS Budgets), and explains when custom Lambda logic is still the better engineering choice.

## Deploying These Functions
Each `lambda_function.py` can be deployed by:
1. Creating the Lambda function in the console (or via `aws lambda create-function`) with the Python 3.12 runtime.
2. Pasting/uploading the corresponding `lambda_function.py` as the deployment package.
3. Creating an IAM role and attaching the corresponding `iam-inline-policy.json` as an inline policy.
4. Setting any required environment variables (see exercise 3's README).
5. Wiring up the corresponding trigger (EventBridge schedule or EventBridge rule, as documented per-exercise).
