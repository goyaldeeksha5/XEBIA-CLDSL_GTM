# Quick Start Guide - GTM Commercial Underwriter Co-Pilot

Get the solution running in minutes for testing and development.

## For Rapid Deployment (Dev Environment)

### Quick Setup (5 minutes)

```bash
# 1. Navigate to project
cd AWS/insurance/commercial-underwriter-copilot

# 2. Build Lambda packages
cd lambda_functions && python3 build.py && cd ..

# 3. Initialize Terraform
terraform init

# 4. Deploy with defaults
terraform apply -auto-approve

# 5. Capture outputs
terraform output > outputs.txt
```

### Test Submission (2 minutes)

```bash
# 1. Create test document
echo "ACME CORPORATION - COMMERCIAL LIABILITY RENEWAL

Policy Number: POL-2024-123456
Insured: ACME Corporation
Coverage: Commercial General Liability
Limits: \$1,000,000 each occurrence / \$2,000,000 aggregate
Deductible: \$10,000
Current Premium: \$5,000
Renewal Date: 06-30-2024

Loss History (Last 3 Years):
- 2023: No losses
- 2022: Fire damage - \$50,000
- 2021: Water damage - \$25,000
" > test_submission.txt

# 2. Upload to S3
BUCKET=$(terraform output -raw submissions_bucket_name)
aws s3 cp test_submission.txt s3://$BUCKET/submissions/sample.txt

# 3. Monitor in CloudWatch
aws logs tail /aws/lambda/GTM_underwriter_copilot-orchestration-agent --follow
```

### View Results (1 minute)

```bash
# Download generated memo
BUCKET=$(terraform output -raw submissions_bucket_name)

# Find the latest submission folder
aws s3 ls s3://$BUCKET/summary/ --recursive

# Download HTML report
aws s3 cp s3://$BUCKET/summary/SUB-*/memo.html ./memo.html
open ./memo.html  # View in browser
```

## Minimal Configuration

For fastest deployment, use defaults:

```bash
# terraform.tfvars (minimal)
aws_region = "us-east-1"
environment = "dev"
```

## Destroy After Testing

```bash
# Clean up all resources
terraform destroy -auto-approve

# Remove local artifacts
rm -rf .terraform terraform.tfstate* tfplan
```

## Troubleshooting Quick Fix

If Lambda functions won't execute:

```bash
# Check function exists
aws lambda list-functions | grep GTM_underwriter_copilot

# Check logs
aws logs describe-log-groups | grep GTM_underwriter_copilot

# Retry deployment
terraform apply
```

## Key Endpoints

After deployment:

- **Submissions Bucket**: `terraform output -raw submissions_bucket_name`
- **Notifications Topic**: `terraform output -raw notifications_topic_arn`
- **Orchestration Lambda**: `terraform output -raw orchestration_agent_function_name`

---

For full deployment details, see [DEPLOYMENT.md](DEPLOYMENT.md)
