# Deployment Guide - GTM Commercial Underwriter Co-Pilot

Complete step-by-step guide to deploy the multi-agent underwriting solution.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Requirements

- AWS Account with appropriate IAM permissions
- Regions: us-east-1 (primary), us-west-2 (optional DR)
- Service quotas for Lambda, S3, SQS, SNS

### Local Development Environment

```bash
# Verify software versions
terraform --version      # >= 1.0
python3 --version       # >= 3.11
aws --version           # >= 2.0

# Install Terraform (if needed)
brew install terraform  # macOS
# or apt-get install terraform  # Linux

# Install AWS CLI (if needed)
pip install --upgrade awscliv2
```

### AWS Bedrock Setup

Ensure Claude 3 model access is enabled:

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Request access if needed
# Go to: AWS Console > Bedrock > Model Access > Request Access
```

### AWS SageMaker (Optional but Recommended)

For risk scoring, set up a SageMaker endpoint:

```bash
# Check existing endpoints
aws sagemaker list-endpoints --region us-east-1

# Create endpoint with your model (outside Terraform scope)
# Reference endpoint name in terraform.tfvars
```

## Pre-Deployment Setup

### Step 1: Clone and Navigate to Project

```bash
cd /workspaces/XEBIA-CLDSL_GTM/AWS/insurance/commercial-underwriter-copilot
tree -L 2  # Verify structure
```

### Step 2: Set AWS Credentials

```bash
# Option A: AWS credentials file
aws configure

# Option B: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Verify credentials
aws sts get-caller-identity
```

### Step 3: Build Lambda Deployment Packages

```bash
cd lambda_functions
python3 build.py

# Output should show:
# ✓ orchestration_agent
# ✓ extraction_agent
# ✓ validation_agent
# ✓ summary_agent

ls -la build/  # Verify .zip files created
cd ..
```

### Step 4: Configure Variables

Create or update `terraform.tfvars`:

```hcl
# AWS Configuration
aws_region = "us-east-1"
environment = "dev"  # or "staging", "prod"

# Project Configuration
project_name = "GTM_underwriter_copilot"

# S3 Configuration
s3_submission_bucket = ""  # Leave empty for auto-generation
submission_prefix = "submissions/"
historical_data_prefix = "historical-data/"
appetite_guide_prefix = "appetite-guides/"

# AI Models
bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
# Alternative models:
# - "anthropic.claude-3-opus-20240229-v1:0" (most capable)
# - "anthropic.claude-3-haiku-20240307-v1:0" (fastest/cheapest)

# SageMaker Configuration (Optional)
sagemaker_endpoint = ""  # e.g., "risk-scoring-endpoint-20240326"

# Lambda Configuration
lambda_timeout = 900      # 15 minutes
lambda_memory = 512       # 512 MB

# Monitoring
enable_monitoring = true
log_retention_days = 30

# Tags
tags = {
  Owner       = "Underwriting-Team"
  CostCenter  = "Insurance"
  Application = "GTM-Underwriter-Copilot"
}
```

## Infrastructure Deployment

### Step 1: Terraform Initialization

```bash
# Initialize Terraform working directory
terraform init

# Output should show:
# Terraform has been successfully configured!

# Verify initialization
terraform version
terraform workspace list  # Show current workspace
```

### Step 2: Review Deployment Plan

```bash
# Generate and review execution plan
terraform plan -out=tfplan

# Key resources to create:
# - 4 Lambda functions
# - 3 SQS queues + 3 DLQs
# - 2 SNS topics
# - 1 S3 bucket
# - 4 IAM roles with policies
# - 4 CloudWatch log groups

# Review the plan carefully
# Look for any unintended deletions or changes
```

### Step 3: Apply Configuration

```bash
# Apply the Terraform configuration
terraform apply tfplan

# Monitor output for:
# - Successfully created resources
# - Any errors or warnings
# - Output values

# Wait for completion (~3-5 minutes)
```

### Step 4: Capture Outputs

```bash
# Extract important outputs
terraform output

# Save outputs for reference:
terraform output -json > deployment_outputs.json

# Key outputs to note:
# - submissions_bucket_name
# - extraction_queue_url
# - validation_queue_url
# - summary_queue_url
# - notifications_topic_arn
```

### Step 5: Verify Deployment

```bash
# List Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'GTM_underwriter_copilot')]"

# List S3 bucket
aws s3 ls | grep GTM_underwriter_copilot

# List SQS queues
aws sqs list-queues --query "QueueUrls[?contains(@, 'GTM_underwriter_copilot')]"

# List SNS topics
aws sns list-topics --query "Topics[?contains(TopicArn, 'GTM_underwriter_copilot')]"
```

## Post-Deployment Configuration

### Step 1: Configure SNS Subscriptions

```bash
# Subscribe to notifications
TOPIC_ARN=$(terraform output -raw notifications_topic_arn)

# Email subscription
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint "underwriting-team@company.com"

# SMS subscription (optional)
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol sms \
  --notification-endpoint "+1234567890"

# Confirm subscription in email
```

### Step 2: Upload Appetite Guidelines

```bash
BUCKET=$(terraform output -raw submissions_bucket_name)

# Create guidelines file
cat > appetite_guidelines.json << 'EOF'
{
  "policy_types": [
    "Commercial General Liability",
    "Commercial Auto",
    "Property",
    "Workers Compensation"
  ],
  "min_coverage_limit": 500000,
  "max_coverage_limit": 5000000,
  "max_loss_ratio": 0.60,
  "max_prior_losses_3_years": 3,
  "min_years_in_business": 2,
  "excluded_industries": [
    "Mining",
    "Aviation",
    "Nuclear",
    "Hazardous Waste"
  ],
  "risk_appetite": {
    "low": {"max_score": 25},
    "medium": {"max_score": 50},
    "high": {"max_score": 75},
    "declined": {"max_score": 100}
  }
}
EOF

# Upload to S3
aws s3 cp appetite_guidelines.json \
  s3://$BUCKET/appetite-guides/guidelines.json
```

### Step 3: Setup S3 Event Notifications

Option A: Using S3 Event Filter (Simple)

```bash
ORCHESTRATION_LAMBDA=$(terraform output -raw orchestration_agent_function_name)
BUCKET=$(terraform output -raw submissions_bucket_name)

# Add S3:PutObject trigger to Lambda
aws lambda create-event-source-mapping \
  --event-source-arn arn:aws:s3:::$BUCKET \
  --function-name $ORCHESTRATION_LAMBDA \
  --events s3:ObjectCreated:Put
```

Option B: Using EventBridge (Recommended)

```bash
# Create EventBridge rule
aws events put-rule \
  --name gtm-underwriter-copilot-submission-rule \
  --event-bus-name default \
  --state ENABLED \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["'$BUCKET'"]
      },
      "object": {
        "key": [{
          "prefix": "submissions/"
        }]
      }
    }
  }'

# Add Lambda as target
aws events put-targets \
  --rule gtm-underwriter-copilot-submission-rule \
  --targets \
    "Id"="1",\
    "Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:$ORCHESTRATION_LAMBDA",\
    "RoleArn"="arn:aws:iam::ACCOUNT_ID:role/service-role/EventBridgeRole"
```

### Step 4: Enable CloudWatch Alarms

```bash
ALERT_TOPIC=$(terraform output -raw alerts_topic_arn)

# Alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name gtm-underwriter-extraction-errors \
  --alarm-description "Alert on Extraction Agent errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions $ALERT_TOPIC \
  --dimensions Name=FunctionName,Value=GTM_underwriter_copilot-extraction-agent
```

## Testing & Validation

### Step 1: Test Individual Agents

#### Test Orchestration Agent

```bash
LAMBDA_NAME=$(terraform output -raw orchestration_agent_function_name)

aws lambda invoke \
  --function-name $LAMBDA_NAME \
  --payload '{
    "document_s3_path": "s3://bucket/test.pdf",
    "file_type": "pdf"
  }' \
  response.json

cat response.json
```

#### Test with Sample Document

```bash
# Create test document
echo "Test Insurance Submission" > test_submission.txt

# Upload to S3
BUCKET=$(terraform output -raw submissions_bucket_name)
aws s3 cp test_submission.txt s3://$BUCKET/submissions/test_submission.txt

# Monitor workflow
watch -n 5 'aws sqs get-queue-attributes \
  --queue-url $(terraform output -raw extraction_queue_url) \
  --attribute-names ApproximateNumberOfMessages'
```

### Step 2: Monitor Execution

```bash
# Watch logs in real-time
aws logs tail /aws/lambda/GTM_underwriter_copilot-orchestration-agent --follow

# In another terminal, check extraction queue
watch -n 2 'aws sqs receive-message \
  --queue-url $(terraform output -raw extraction_queue_url) | jq .'
```

### Step 3: Verify Output Artifacts

```bash
BUCKET=$(terraform output -raw submissions_bucket_name)

# List all workflow artifacts
aws s3 ls s3://$BUCKET/ --recursive

# Download summary memo
aws s3 cp \
  s3://$BUCKET/summary/SUB-20240326-XXXXX/memo.html \
  local_memo.html

# View in browser
open local_memo.html
```

## Troubleshooting

### Issue: Lambda Function Timeout

```bash
# Check Lambda logs
aws logs tail /aws/lambda/GTM_underwriter_copilot-orchestration-agent --follow

# Increase timeout in terraform.tfvars
lambda_timeout = 1800  # 30 minutes

# Redeploy
terraform apply
```

### Issue: SQS Message Not Processing

```bash
# Check queue visibility
aws sqs receive-message \
  --queue-url $(terraform output -raw extraction_queue_url) \
  --max-number-of-messages 10

# Check DLQ for failed messages
aws sqs receive-message \
  --queue-url $(terraform output -raw extraction_dlq_url) \
  --max-number-of-messages 10

# Check Lambda concurrency limits
aws lambda get-account-settings
```

### Issue: Bedrock Model Access Denied

```bash
# Verify model access enabled
aws bedrock list-foundation-models --query "modelSummaries[?modelId=='anthropic.claude-3-sonnet-20240229-v1:0']"

# Request access in AWS Console if needed
# Services > Bedrock > Model Access > Request Model Access

# Switch to alternative model in terraform.tfvars
bedrock_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
```

### Issue: S3 Permissions Error

```bash
# Verify bucket policy
aws s3api get-bucket-policy --bucket $(terraform output -raw submissions_bucket_name)

# Verify Lambda role permissions
aws iam get-role-policy \
  --role-name GTM_underwriter_copilot-extraction-agent-role \
  --policy-name GTM_underwriter_copilot-s3-access-policy
```

## Rollback Procedure

If something goes wrong:

```bash
# Save current state
cp terraform.tfstate terraform.tfstate.backup

# Destroy infrastructure
terraform destroy

# Review what will be deleted
# Confirm when prompted

# Optional: Restore specific resources from backup
terraform apply -target=resource ...
```

## Performance Baseline

Initial deployment performance metrics:

| Operation | Time | Notes |
|-----------|------|-------|
| Terraform Init | ~1 min | Initial setup |
| Plan | ~10 sec | Dependency analysis |
| Apply | 3-5 min | Resource creation |
| Lambda Cold Start | 1-2 sec | Python 3.11 |
| Textract OCR | 5-30 sec | Depends on document size |
| Bedrock Inference | 2-5 sec | Token generation |
| SageMaker Scoring | 1-3 sec | Endpoint response |
| End-to-End Workflow | 1-3 min | Full submission processing |

## Next Steps

1. **Scale Configuration**: Increase `agents_count` for higher throughput
2. **Fine-tune Models**: Customize Bedrock prompts for your business
3. **Integrate CRM**: Connect to underwriting management system
4. **Add Dashboard**: Build monitoring dashboard in CloudWatch
5. **Cost Optimization**: Set up Cost Anomaly Detection

## Support

For deployment issues:

1. Check CloudWatch logs
2. Review AWS service quotas
3. Verify IAM permissions
4. Test with simpler payloads
5. Contact AWS Support

---

**Deployment Version**: 1.0
**Last Updated**: March 26, 2024
