# Dynamic Pricing Rating Engine - Deployment Guide

## Architecture Overview

The Dynamic Pricing Rating Engine consists of 5 layers:

### 1. **Data Stream Layer** (Amazon Timestream)
- Database: `GTM_insurance_dynamicpricing_ratingengine`
- Table: `GTM_insurance_dynamicpricing_ratingengine_Telematics`
- Stores time-series telematics data with retention policies

### 2. **State & Approval Layer** (DynamoDB)
- Table: `GTM_insurance_dynamicpricing_ratingengine_Proposals`
- Stores proposal data with stream enabled for real-time processing
- Key: `ProposalID`

### 3. **Execution Layer** (AWS Lambda)
- Function: `GTM_insurance_dynamicpricing_ratingengine_Gateway`
- Runtime: Python 3.12
- Timeout: 60 seconds
- Processes proposals and interacts with Timestream and DynamoDB

### 4. **Orchestration Layer** (EventBridge)
- Rule: `GTM_insurance_dynamicpricing_ratingengine_RiskSignal`
- Triggers Lambda on risk anomalies and competitor shifts

### 5. **Permissions & IAM**
- Lambda execution role with permissions for:
  - DynamoDB read/write
  - Timestream write
  - CloudWatch Logs

## Prerequisites

1. **AWS Account Setup**
   - AWS credentials configured: `aws configure`
   - Account ID: `474532148129`

2. **Terraform Backend**
   - S3 bucket: `xebia-cldsl-gtm-terraform-state-474532148129`
   - DynamoDB lock table: `xebia-cldsl-gtm-terraform-locks`
   - ✅ Already created and enabled

3. **Lambda Code Package**
   - Create a `lambda_function_payload.zip` file in the `DynamicPricing_Rating_engine/` directory
   - Must contain `index.py` with `lambda_handler` function

## Lambda Function Template

If you don't have Lambda code yet, here's a basic template:

### Create `DynamicPricing_Rating_engine/index.py`:
```python
import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
timestream_client = boto3.client('timestream-write')

PROPOSAL_TABLE = os.environ['PROPOSAL_TABLE']
DATABASE_NAME = os.environ['DATABASE_NAME']
TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    """
    Handles proposal processing and pricing decisions
    """
    try:
        print(f"Event: {json.dumps(event)}")
        
        # Extract proposal from event
        detail = event.get('detail', {})
        proposal_id = detail.get('proposal_id')
        risk_level = detail.get('severity')
        
        # Store proposal in DynamoDB
        table = dynamodb.Table(PROPOSAL_TABLE)
        table.put_item(Item={
            'ProposalID': proposal_id,
            'RiskLevel': risk_level,
            'Timestamp': datetime.now().isoformat(),
            'Status': 'PROCESSING'
        })
        
        # Write metrics to Timestream (optional)
        # timestream_client.write_records(...)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Proposal processed successfully',
                'proposal_id': proposal_id
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Create the ZIP file:
```bash
cd DynamicPricing_Rating_engine/
zip lambda_function_payload.zip index.py
cd ..
```

## Deployment Steps

### Step 1: Reinitialize Terraform with Remote Backend
```bash
terraform init
```

### Step 2: Plan Deployment
```bash
terraform plan
```

### Step 3: Apply Configuration
```bash
terraform apply
```

This will create:
- ✅ Timestream database and table
- ✅ DynamoDB proposals table
- ✅ Lambda function
- ✅ EventBridge rule
- ✅ IAM roles and policies

### Step 4: Verify Deployment
```bash
# List created resources
aws dynamodb list-tables
aws lambda list-functions
aws events list-rules

# Check Lambda function
aws lambda get-function --function-name GTM_insurance_dynamicpricing_ratingengine_Gateway
```

## Configuration Options

Modify [variables.tf](DynamicPricing_Rating_engine/variables.tf) to customize:

```hcl
# Timestream retention
timestream_retention_memory_hours  = 24    # hours
timestream_retention_magnetic_days = 365   # days

# Lambda configuration
lambda_timeout  = 60        # seconds
lambda_runtime  = "python3.12"

# Project naming
project_name = "GTM_insurance_dynamicpricing_ratingengine"
environment  = "production"
```

## Testing EventBridge Trigger

```bash
# Send test event to EventBridge
aws events put-events --entries '[
  {
    "Source": "gtm.insurance.signals",
    "DetailType": "RiskAnomalyDetected",
    "Detail": "{\"proposal_id\": \"PROP-001\", \"severity\": \"HIGH\"}"
  }
]'

# Check Lambda logs
aws logs tail /aws/lambda/GTM_insurance_dynamicpricing_ratingengine_Gateway --follow
```

## Common Issues & Troubleshooting

### Lambda Execution Fails
**Problem**: Lambda times out or fails to execute  
**Solution**:
1. Check IAM permissions: `aws iam get-role --role-name GTM_insurance_dynamicpricing_ratingengine_LambdaRole`
2. Review Lambda logs: `aws logs describe-log-groups --query 'logGroups[?contains(logGroupName, `GTM`)].logGroupName'`
3. Verify Lambda package exists: `ls -la DynamicPricing_Rating_engine/lambda_function_payload.zip`

### DynamoDB Access Denied
**Problem**: Lambda can't write to DynamoDB  
**Solution**:
1. Verify IAM policy is attached
2. Check table name environment variable matches actual table

### EventBridge Rule Not Triggering
**Problem**: Lambda function not invoked by EventBridge  
**Solution**:
1. Check rule is enabled: `aws events describe-rule --name GTM_insurance_dynamicpricing_ratingengine_RiskSignal`
2. Verify Lambda permission: `aws lambda get-policy --function-name GTM_insurance_dynamicpricing_ratingengine_Gateway`

## Cleanup

To remove all resources:
```bash
# Destroy infrastructure (but keep Terraform state and backend)
terraform destroy

# To also remove state files (be careful!)
rm -f terraform.tfstate*
rm -rf .terraform/
```

## File Structure

```
XEBIA-CLDSL_GTM/
├── main.tf                              # Root module (calls dynamic_pricing module)
├── provider.tf                          # AWS provider with S3 backend
├── variables.tf                         # Root variables
├── terraform.tfvars                     # Variable values
├── backend.tf                           # S3 bucket and DynamoDB lock table
├── backend-config.hcl                   # Backend configuration
├── BACKEND_SETUP.md                     # Backend setup guide
├── DEPLOYMENT_GUIDE.md                  # This file
├── DynamicPricing_Rating_engine/
│   ├── main.tf                          # Core resources (Timestream, DynamoDB, Lambda, EventBridge)
│   ├── iam.tf                           # IAM roles and policies
│   ├── variables.tf                     # Module variables
│   ├── outputs.tf                       # Module outputs
│   ├── lambda_function_payload.zip      # Lambda code (create this)
│   └── index.py                         # Lambda handler (create this)
└── DynamicPricing_Rating_engine/        # Existing resources
    └── main.tf
```

## Next Steps

1. ✅ Deploy Terraform configuration: `terraform apply`
2. Create Lambda function code and ZIP file
3. Test EventBridge triggers
4. Monitor Lambda execution through CloudWatch logs
5. Add additional modules (additional services, ML models, etc.)
