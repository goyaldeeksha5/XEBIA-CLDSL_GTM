# Deployment Guide - GTM Dynamic Pricing & Continuous Rating Engine

Complete step-by-step guide to deploy the dynamic pricing and continuous rating engine to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Testing & Validation](#testing--validation)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### AWS Account Requirements

- AWS Account with appropriate IAM permissions
- Regions: us-east-1 (primary), us-west-2 (optional DR)
- Service quotas verified:
  - Lambda: 1000 concurrent execution limit
  - DynamoDB: On-demand or provisioned capacity
  - EventBridge: 100 rules minimum
  - SageMaker: Endpoint access (if using risk scoring)
  - Bedrock: Claude 3+ model access enabled

### Required AWS Services Access

```bash
# Enable Bedrock model access (if not already enabled)
# Go to: AWS Console > Bedrock > Model Access > Request Access
# Select: Claude 3 Opus / Sonnet / Haiku

# Verify SageMaker endpoint exists (optional)
aws sagemaker list-endpoints --region us-east-1

# Verify Textract/Comprehend are accessible (optional)
aws textract get-document-text-detection \
  --document '{"Bytes": "test"}' || echo "Textract available"
```

### Local Development Environment

```bash
# Verify software versions
terraform --version      # >= 1.0
python3 --version       # >= 3.11
aws --version           # >= 2.0
git --version           # >= 2.0

# Install Terraform (if needed)
# macOS:
brew install terraform

# Linux (Ubuntu/Debian):
sudo apt-get install terraform

# Install AWS CLI v2 (if needed)
# macOS:
brew install awscliv2

# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## Pre-Deployment Setup

### Step 1: Clone and Navigate to Project

```bash
cd /workspaces/XEBIA-CLDSL_GTM/AWS/insurance/dynamic-pricing-continuous-rating-engine

# Verify structure
ls -la
tree -L 2

# Expected files:
# ├── main.tf
# ├── variables.tf
# ├── iam.tf
# ├── outputs.tf
# ├── provider.tf
# ├── index.py
# ├── openapi.yaml
# ├── terraform.tfvars (or create)
# └── README.md
```

### Step 2: Set AWS Credentials

```bash
# Option A: AWS credentials file
aws configure

# Follow prompts for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json

# Option B: Environment variables (for CI/CD)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Verify credentials
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

### Step 3: Review and Customize terraform.tfvars

```bash
# If terraform.tfvars doesn't exist, create it
cat > terraform.tfvars << 'EOF'
# Core Configuration
aws_region   = "us-east-1"
environment  = "dev"
project_name = "GTM_Dynamic-Pricing-Continuous-Rating-Engine"

# Optional: Advanced Configuration
enable_sagemaker_scoring = false  # Set to true if using SageMaker
sagemaker_endpoint_name  = ""     # Your SageMaker endpoint name
enable_bedrock_reasoning = true   # Bedrock analysis enabled by default

# Monitoring
cloudwatch_retention_days = 30
alarm_email               = "your-team-email@company.com"

# DynamoDB Settings
dynamodb_billing_mode = "PAY_PER_REQUEST"  # or "PROVISIONED"
telematics_table_ttl  = 2592000            # 30 days in seconds

# SNS/SQS Settings
enable_sns_notifications = true
enable_sqs_queue        = true
EOF

# For Production, use more restrictive settings:
cat > terraform.tfvars.prod << 'EOF'
aws_region   = "us-east-1"
environment  = "prod"
project_name = "GTM_Dynamic-Pricing-Continuous-Rating-Engine-Prod"

enable_sagemaker_scoring = true
sagemaker_endpoint_name  = "pricing-risk-scorer-prod"

cloudwatch_retention_days = 90
alarm_email               = "ops-team@company.com"

dynamodb_billing_mode = "PROVISIONED"
enable_sns_notifications = true
enable_sqs_queue        = true
EOF
```

### Step 4: Build Lambda Deployment Package

```bash
# Option 1: Simple package (just index.py)
python3 << 'EOF'
import zipfile
import os

zip_file = 'lambda_function_payload.zip'
if os.path.exists(zip_file):
    os.remove(zip_file)

with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write('index.py')

print(f"✓ Created {zip_file}")
with zipfile.ZipFile(zip_file, 'r') as z:
    print(f"  Contents: {z.namelist()}")
EOF

# Option 2: Include dependencies (if needed)
python3 << 'EOF'
import zipfile
import os
import subprocess

zip_file = 'lambda_function_payload.zip'
if os.path.exists(zip_file):
    os.remove(zip_file)

# Create package directory
os.makedirs('package', exist_ok=True)

# Install dependencies
subprocess.run([
    'pip', 'install', 
    '-t', 'package/',
    'boto3==1.28.0',  # Already in Lambda, but for reference
    'requests==2.31.0'
], check=True)

# Create zipfile
with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('package'):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, 'package')
            zipf.write(file_path, arcname)
    zipf.write('index.py')

print(f"✓ Created {zip_file} with dependencies")
EOF

# Verify package
unzip -l lambda_function_payload.zip | head -20
```

### Step 5: Review IAM Policies

```bash
# Review what IAM roles will be created
cat iam.tf | head -50

# Key roles created:
# - Lambda execution role (DynamoDB, CloudWatch, Bedrock access)
# - EventBridge role (Lambda invocation)
# - SQS/SNS permissions

# For production, consider:
# - IP whitelisting
# - VPC endpoint access
# - KMS encryption
```

## Infrastructure Deployment

### Step 1: Initialize Terraform

```bash
# Initialize Terraform working directory
terraform init

# Expected output:
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully configured!

# Verify backend state
ls -la .terraform/
```

### Step 2: Plan Deployment

```bash
# Generate execution plan
# Development:
terraform plan -out=tfplan

# Production (use prod vars):
terraform plan -var-file=terraform.tfvars.prod -out=tfplan

# Review the plan output which shows:
# - Resources to create
# - Estimated costs
# - Changes to existing resources

# Verify key resources:
grep -E "aws_lambda_function|aws_dynamodb_table|aws_api_gateway" tfplan || \
  terraform plan | grep -E "will be created|created|destroyed"
```

### Step 3: Apply Deployment

```bash
# Apply the plan (dev)
terraform apply tfplan

# Or apply with auto-approval (dev only!)
terraform apply -auto-approve

# For production, use explicit plan:
terraform apply tfplan.prod

# Wait for completion (typically 3-5 minutes)
# Expected output shows:
# - All resources created
# - Outputs section with API endpoint, table names, etc.
```

### Step 4: Capture and Verify Outputs

```bash
# Save all outputs
terraform output > deployment-outputs.txt

# Export critical values to environment
export API_ENDPOINT=$(terraform output -raw api_gateway_url)
export API_KEY=$(terraform output -raw api_key)
export PROPOSALS_TABLE=$(terraform output -raw proposals_table_name)
export TELEMATICS_TABLE=$(terraform output -raw telematics_table_name)

# Verify outputs
echo "API Endpoint: $API_ENDPOINT"
echo "Proposals Table: $PROPOSALS_TABLE"
echo "Telematics Table: $TELEMATICS_TABLE"

# Verify resources in AWS Console
terraform show | grep -E "arn:|id ="
```

## Post-Deployment Configuration

### Step 1: Configure EventBridge Rules

```bash
# Verify EventBridge rule created
aws events list-rules \
  --region us-east-1 | grep -i dynamic

# Get rule details
RULE_NAME=$(terraform output -raw eventbridge_rule_name)
aws events describe-rule \
  --name "$RULE_NAME" \
  --region us-east-1

# Test rule manually
aws events put-events \
  --entries file://test-signal.json \
  --region us-east-1
```

### Step 2: Configure SNS Notifications

```bash
# List SNS topics created
aws sns list-topics --region us-east-1 | grep -i dynamic

# Subscribe email to notifications
TOPIC_ARN=$(terraform output -raw sns_topic_arn)
aws sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "your-email@company.com" \
  --region us-east-1

# Confirm subscription in email
```

### Step 3: Configure SageMaker (if using risk scoring)

```bash
# If enable_sagemaker_scoring = true, configure endpoint:
ENDPOINT_NAME="pricing-risk-scorer-dev"

# Test endpoint connectivity
aws sagemaker describe-endpoint \
  --endpoint-name "$ENDPOINT_NAME" \
  --region us-east-1

# If not found, create SageMaker endpoint (outside Terraform scope)
# See SageMaker documentation for model deployment
```

### Step 4: Configure API Gateway Authentication

```bash
# Update API Gateway to use API key restriction
API_ID=$(terraform output -raw api_gateway_id)
STAGE="prod"

# Create usage plan
aws apigateway create-usage-plan \
  --name gtm-pricing-usage-plan \
  --description "Usage plan for GTM pricing engine" \
  --api-stages apiId=$API_ID,stage=$STAGE \
  --region us-east-1

# Create API key
KEY_DETAILS=$(aws apigateway create-api-key \
  --name gtm-pricing-api-key \
  --enabled \
  --region us-east-1)

echo "API Key details saved - verify in outputs.txt"
```

## Testing & Validation

### Step 1: Health Check

```bash
# Test API health endpoint
curl -s "$API_ENDPOINT/health" \
  -H "X-API-Key: $API_KEY" | jq .

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "dynamodb": "ok",
#     "bedrock": "ok",
#     "lambda": "ok"
#   },
#   "timestamp": "2024-03-26T..."
# }
```

### Step 2: Submit Test Pricing Simulation

```bash
# Create test event
cat > test-pricing-event.json << 'EOF'
{
  "policy_id": "FL-992-APEX",
  "current_premium": 125000,
  "telematics_score": 72,
  "metadata": {
    "vehicle_age": 3,
    "annual_mileage": 12500
  }
}
EOF

# Submit via API
curl -s -X POST "$API_ENDPOINT/pricing/simulate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d @test-pricing-event.json | jq .

# Or submit via EventBridge
aws events put-events \
  --entries file://test-pricing-event.json \
  --region us-east-1
```

### Step 3: Verify Proposal Creation

```bash
# Wait 2-3 minutes for processing
sleep 180

# Query proposals table
aws dynamodb scan \
  --table-name "$PROPOSALS_TABLE" \
  --region us-east-1 \
  --limit 5 | jq '.Items[] | { ProposalID, Status, ProposedPremium }'

# Get specific proposal details
PROPOSAL_ID=$(aws dynamodb scan --table-name "$PROPOSALS_TABLE" --region us-east-1 --limit 1 | jq -r '.Items[0].ProposalID.S')

aws dynamodb get-item \
  --table-name "$PROPOSALS_TABLE" \
  --key "{\"ProposalID\": {\"S\": \"$PROPOSAL_ID\"}}" \
  --region us-east-1 | jq .Item
```

### Step 4: Load Testing

```bash
# Submit batch of proposals (load test)
python3 << 'EOF'
import requests
import json
import sys

api_key = sys.argv[1] if len(sys.argv) > 1 else ""
api_endpoint = sys.argv[2] if len(sys.argv) > 2 else ""

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

for i in range(10):
    payload = {
        "policy_id": f"POL-{i:06d}",
        "current_premium": 100000 + (i * 5000),
        "telematics_score": 60 + (i % 40)
    }
    
    try:
        response = requests.post(
            f"{api_endpoint}/pricing/simulate",
            json=payload,
            headers=headers,
            timeout=10
        )
        print(f"POL-{i:06d}: {response.status_code}")
    except Exception as e:
        print(f"POL-{i:06d}: ERROR - {e}")

EOF

# Run load test
python3 load_test.py "$API_KEY" "$API_ENDPOINT"
```

## Monitoring & Alerts

### Step 1: Configure CloudWatch Dashboards

```bash
# Create basic dashboard
aws cloudwatch put-dashboard \
  --dashboard-name GTM-Pricing-Engine-Monitoring \
  --dashboard-body file://dashboard-config.json \
  --region us-east-1

# Example dashboard JSON:
cat > dashboard-config.json << 'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", {"stat": "Average"}],
          ["AWS/Lambda", "Errors", {"stat": "Sum"}],
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "GTM Pricing Engine Metrics"
      }
    }
  ]
}
EOF
```

### Step 2: Configure CloudWatch Alarms

```bash
# Lambda Error Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name GTM-Pricing-Lambda-Errors \
  --alarm-description "Alert on Lambda execution errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions "arn:aws:sns:us-east-1:ACCOUNT:gtm-pricing-alerts" \
  --region us-east-1

# DynamoDB Throttling Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name GTM-Pricing-DynamoDB-Throttle \
  --alarm-description "Alert on DynamoDB throttling" \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions "arn:aws:sns:us-east-1:ACCOUNT:gtm-pricing-alerts" \
  --region us-east-1
```

### Step 3: Enable CloudTrail Logging

```bash
# Enable audit logging for compliance
aws cloudtrail create-trail \
  --name gtm-pricing-audit-trail \
  --s3-bucket-name gtm-pricing-audit-logs \
  --is-multi-region-trail \
  --region us-east-1

# Start logging
aws cloudtrail start-logging \
  --trail-name gtm-pricing-audit-trail \
  --region us-east-1
```

## Troubleshooting

### Lambda Functions Not Executing

**Symptoms:** Events submitted but no proposals created.

```bash
# 1. Verify Lambda function exists
aws lambda list-functions \
  --region us-east-1 | grep -i pricing

# 2. Check Lambda execution role
FUNCTION_NAME=$(terraform output -raw lambda_function_name)
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region us-east-1 | jq .Configuration.Role

# 3. Test Lambda directly
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{"detail": {"policy_id": "TEST", "current_premium": 10000, "telematics_score": 50}}' \
  --region us-east-1 \
  response.json
```

### DynamoDB Table Issues

**Symptoms:** Proposals not being saved or table errors.

```bash
# 1. Verify table exists and is active
aws dynamodb describe-table \
  --table-name "$PROPOSALS_TABLE" \
  --region us-east-1 | jq '.Table | {TableName, TableStatus, BillingModeSummary}'

# 2. Check DynamoDB Streams enabled
aws dynamodb describe-table \
  --table-name "$TELEMATICS_TABLE" \
  --region us-east-1 | jq '.Table.StreamSpecification'

# 3. Scale table if provisioned
if [ "$(jq '.Table.BillingModeSummary.BillingMode' ...)" == '"PROVISIONED"' ]; then
  aws dynamodb update-table \
    --table-name "$PROPOSALS_TABLE" \
    --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=100 \
    --region us-east-1
fi

# 4. Check for throttling
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value="$PROPOSALS_TABLE" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

### EventBridge Not Triggering

**Symptoms:** Manual API calls work but EventBridge events don't trigger Lambda.

```bash
# 1. Verify rule exists and is enabled
aws events describe-rule \
  --name $(terraform output -raw eventbridge_rule_name) \
  --region us-east-1 | jq '{Name, State}'

# 2. Check targets
aws events list-targets-by-rule \
  --rule $(terraform output -raw eventbridge_rule_name) \
  --region us-east-1

# 3. Enable rule if disabled
aws events enable-rule \
  --name $(terraform output -raw eventbridge_rule_name) \
  --region us-east-1

# 4. Test EventBridge manually
aws events put-events \
  --entries '[{
    "Source": "custom.insurance",
    "DetailType": "Telematics Signal",
    "Detail": "{\"policy_id\": \"TEST\", \"current_premium\": 10000, \"telematics_score\": 50}"
  }]' \
  --region us-east-1
```

### Bedrock Access Denied

**Symptoms:** Lambda execution fails with "Bedrock access denied" error.

```bash
# 1. Verify Bedrock model access enabled
aws bedrock list-foundation-models --region us-east-1

# 2. Check Lambda execution role permissions
ROLE_ARN=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region us-east-1 | jq -r .Configuration.Role)
aws iam get-role-policy \
  --role-name $(echo $ROLE_ARN | awk -F'/' '{print $NF}') \
  --policy-name bedrock-access \
  --region us-east-1

# 3. If missing, add permissions (manual)
# Edit iam.tf and add:
# resource "aws_iam_role_policy" "lambda_bedrock" {
#   role   = aws_iam_role.lambda_exec_role.id
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect = "Allow"
#       Action = ["bedrock:Invoke*"]
#       Resource = "*"
#     }]
#   })
# }

terraform apply -auto-approve
```

### API Gateway Authorization Failures

**Symptoms:** API calls fail with 401 Unauthorized.

```bash
# 1. Verify API key exists
aws apigateway get-api-keys --region us-east-1

# 2. Verify API key is enabled
API_KEY_ID=$(terraform output -raw api_key_id)
aws apigateway get-api-key \
  --api-key "$API_KEY_ID" \
  --include-value \
  --region us-east-1

# 3. Verify usage plan attached to stage
aws apigateway get-usage-plans --region us-east-1

# 4. Test with correct header
curl "$API_ENDPOINT/health" \
  -H "X-API-Key: $API_KEY" \
  -v  # verbose to see headers
```

### High Latency/Performance Issues

**Symptoms:** Pricing simulations take > 5 minutes.

```bash
# 1. Check Lambda memory allocation
aws lambda get-function-concurrency \
  --function-name "$FUNCTION_NAME" \
  --region us-east-1

# Increase memory (improves CPU):
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --memory-size 1024 \
  --region us-east-1

# 2. Check DynamoDB capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value="$PROPOSALS_TABLE" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum \
  --region us-east-1

# 3. Check Lambda duration
aws logs filter-log-events \
  --log-group-name /aws/gtm/Dynamic-Pricing-Continuous-Rating-Engine \
  --filter "[., request_id, event, timestamp, bytes, request_id]" \
  --region us-east-1
```

## Rollback Procedure

If deployment fails or issues arise:

```bash
# 1. Destroy all resources
terraform destroy -auto-approve

# 2. Clean up local state
rm -rf .terraform terraform.tfstate* tfplan

# 3. Re-deploy with fixes
# Make necessary changes to .tf files, then:
terraform init
terraform apply -auto-approve
```

## Next Steps

1. **Configure Auto-Scaling**: See CloudWatch docs for Lambda concurrency auto-scaling
2. **Setup CI/CD Pipeline**: Automate deployments using GitHub Actions or CodePipeline
3. **Enable VPC Integration**: For production, deploy Lambda in VPC with privatelink access
4. **Setup Disaster Recovery**: Configure multi-region failover and backup strategy
5. **Performance Tuning**: Implement caching, connection pooling, and model optimization

---

**Need help?** See [README.md](README.md) for architecture details or [QUICKSTART.md](QUICKSTART.md) for rapid testing.
