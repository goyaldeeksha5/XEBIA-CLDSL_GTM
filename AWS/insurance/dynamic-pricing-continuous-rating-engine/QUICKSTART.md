# Quick Start Guide - GTM Dynamic Pricing & Continuous Rating Engine

Get the Dynamic Pricing Engine running in minutes for testing and development.

## For Rapid Deployment (Dev Environment)

### Quick Setup (5 minutes)

```bash
# 1. Navigate to project
cd AWS/insurance/dynamic-pricing-continuous-rating-engine

# 2. Build Lambda function
python3 -c "import zipfile; z = zipfile.ZipFile('lambda_function_payload.zip', 'w'); z.write('index.py')"

# 3. Initialize Terraform
terraform init

# 4. Deploy with defaults
terraform apply -auto-approve

# 5. Capture outputs
terraform output > outputs.txt
```

### Test Pricing Simulation (3 minutes)

```bash
# 1. Create test event file (test-signal.json)
cat > test-signal.json << 'EOF'
{
  "version": "0",
  "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
  "detail-type": "Telematics Signal",
  "source": "custom.insurance",
  "account": "123456789012",
  "time": "2024-03-26T10:30:45Z",
  "region": "us-east-1",
  "detail": {
    "policy_id": "FL-992-APEX",
    "current_premium": 125000,
    "telematics_score": 72,
    "vehicle_age": 3,
    "annual_mileage": 12500,
    "driver_tenure": 8,
    "claims_count": 0
  }
}
EOF

# 2. Submit event using AWS CLI
aws events put-events \
  --entries file://test-signal.json \
  --region us-east-1

# 3. View Lambda execution logs
aws logs tail /aws/gtm/Dynamic-Pricing-Continuous-Rating-Engine --follow
```

### View Generated Proposals (2 minutes)

```bash
# 1. Get table name from outputs
TABLE_NAME=$(grep "proposals_table_name" outputs.txt | awk '{print $NF}' | tr -d '"')
echo "Using table: $TABLE_NAME"

# 2. Scan for recent proposals
aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region us-east-1 \
  --limit 5

# 3. Alternative: Get specific proposal (if you know the ID)
aws dynamodb get-item \
  --table-name "$TABLE_NAME" \
  --key '{"ProposalID": {"S": "abc12345"}}' \
  --region us-east-1
```

## Minimal Configuration

For fastest deployment, use these defaults:

```bash
# terraform.tfvars (minimal)
aws_region   = "us-east-1"
environment  = "dev"
project_name = "GTM_Dynamic-Pricing-Continuous-Rating-Engine"
```

If `terraform.tfvars` doesn't exist, create it:

```bash
cat > terraform.tfvars << 'EOF'
aws_region   = "us-east-1"
environment  = "dev"
project_name = "GTM_Dynamic-Pricing-Continuous-Rating-Engine"
EOF
```

## Common Tasks

### Deploy and Get API Endpoint
```bash
terraform apply -auto-approve

# Get API Gateway URL
API_ENDPOINT=$(terraform output -raw api_gateway_url)
echo "API Endpoint: $API_ENDPOINT"
```

### Submit Pricing Request via API
```bash
API_ENDPOINT=$(terraform output -raw api_gateway_url)
API_KEY=$(terraform output -raw api_key)

curl -X POST "$API_ENDPOINT/pricing/simulate" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": "FL-992-APEX",
    "current_premium": 125000,
    "telematics_score": 72
  }'
```

### Check Proposal Status
```bash
API_ENDPOINT=$(terraform output -raw api_gateway_url)
API_KEY=$(terraform output -raw api_key)
PROPOSAL_ID="PROP-20240326-A1B2C3"  # From previous submission

curl -X GET "$API_ENDPOINT/proposal/$PROPOSAL_ID" \
  -H "X-API-Key: $API_KEY"
```

### Monitor in Real-Time
```bash
# Terminal 1: Watch Lambda logs
aws logs tail /aws/gtm/Dynamic-Pricing-Continuous-Rating-Engine --follow

# Terminal 2: Watch DynamoDB proposals
TABLE_NAME=$(grep "proposals_table_name" outputs.txt | awk '{print $NF}' | tr -d '"')

while true; do
  aws dynamodb scan \
    --table-name "$TABLE_NAME" \
    --region us-east-1 \
    --limit 3 \
    --projection-expression "ProposalID, #status, ProposedPremium" \
    --expression-attribute-names '{"#status": "Status"}'
  sleep 5
  clear
done
```

### Access DynamoDB Console
```bash
# Get table names to access directly
terraform output

# Open AWS Console in browser (replace with your region/account)
open "https://console.aws.amazon.com/dynamodb/home?region=us-east-1#tables:"
```

## Troubleshooting Quick Fix

### Lambda Functions Not Executing

```bash
# 1. Check Lambda exists
aws lambda list-functions \
  --region us-east-1 | grep Dynamic-Pricing

# 2. Check execution role
aws lambda get-function \
  --function-name GTM_Dynamic-Pricing-Continuous-Rating-Engine-pricing-agent \
  --region us-east-1 | grep Role

# 3. Check for errors in logs
aws logs describe-log-groups \
  --region us-east-1 | grep Dynamic-Pricing

# 4. Re-deploy Lambda package
python3 -c "import zipfile; z = zipfile.ZipFile('lambda_function_payload.zip', 'w'); z.write('index.py')"
terraform apply -auto-approve
```

### DynamoDB Table Issues

```bash
# 1. Verify table exists
TABLE_NAME=$(terraform output -raw proposals_table_name)
aws dynamodb describe-table \
  --table-name "$TABLE_NAME" \
  --region us-east-1

# 2. Check table capacity
aws dynamodb describe-table \
  --table-name "$TABLE_NAME" \
  --region us-east-1 | grep -A 5 "BillingModeSummary"

# 3. Scan for data
aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region us-east-1 \
  --limit 10
```

### Permissions/Access Issues

```bash
# 1. Verify AWS credentials
aws sts get-caller-identity

# 2. Check IAM user permissions
aws iam get-user

# 3. List attached policies
aws iam list-attached-user-policies \
  --user-name <your-username>
```

### EventBridge Not Triggering Lambda

```bash
# 1. Check EventBridge rules exist
aws events list-rules \
  --region us-east-1 | grep Dynamic-Pricing

# 2. Check rule details
aws events describe-rule \
  --name gtm-telematics-signal-rule \
  --region us-east-1

# 3. List targets for rule
aws events list-targets-by-rule \
  --rule gtm-telematics-signal-rule \
  --region us-east-1

# 4. Enable rule if disabled
aws events enable-rule \
  --name gtm-telematics-signal-rule \
  --region us-east-1
```

## Destroy After Testing

```bash
# 1. Destroy all resources
terraform destroy -auto-approve

# 2. Remove local artifacts
rm -rf .terraform terraform.tfstate* tfplan lambda_function_payload.zip outputs.txt test-signal.json
```

## Next Steps

After confirming the quick deploy works:

1. **Read the API Documentation** - See [API.md](API.md) for full endpoint details
2. **Review the Deployment Guide** - See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
3. **Understand the Architecture** - See [README.md](README.md) for detailed workflow information
4. **Configure Monitoring** - Set up CloudWatch dashboards and alerts
5. **Integration Testing** - Connect to your policy management system

## Common Questions

**Q: How long does pricing simulation take?**
A: Typically 2-3 minutes from submission to completed proposal in DynamoDB.

**Q: Can I test without AWS credentials?**
A: No, AWS credentials with appropriate IAM permissions are required.

**Q: Is DynamoDB on-demand pricing expensive?**
A: For dev/test, pay-per-request is cost-effective. For production, consider provisioned capacity.

**Q: How do I access the HTML proposal report?**
A: Reports are stored in S3. Use the AWS Console or `aws s3 cp` to download.

**Q: What's included in the proposal rationale?**
A: Bedrock generates natural language reasoning based on telematics scores, market data, and risk factors.

## Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
2. Review [README.md](README.md) for architecture details
3. Contact GTM engineering team

---

**Ready to go deeper?** See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment procedures.
