# Bedrock Agent Setup Guide

## Overview

This guide walks through setting up the **GTM Dynamic Pricing Agent** in Amazon Bedrock to power the insurance rating system.

## Prerequisites

✅ AWS Account with Bedrock access enabled  
✅ IAM permissions to create Bedrock Agents  
✅ Lambda function deployed: `GTM_insurance_dynamicpricing_ratingengine_Gateway`  
✅ OpenAPI spec available at: `DynamicPricing_Rating_engine/openapi.yaml`

## Step-by-Step Setup

### Step 1: Enable Bedrock (if not already enabled)

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Click **Get Started** (if not enabled)
3. Accept the service terms
4. In left sidebar, click **Models** and enable:
   - ✅ Claude 3 Sonnet (model-id: `anthropic.claude-3-sonnet-20240229-v1:0`)

### Step 2: Create Bedrock Agent

#### 2.1 Navigate to Agents

1. Go to AWS Bedrock Console
2. In left sidebar, click **Agents** (under **Build**)
3. Click **Create agent**

#### 2.2 Agent Configuration

| Field | Value |
|-------|-------|
| **Agent name** | `GTM-Dynamic-Pricing-Agent` |
| **Agent description** | `Evaluates insurance risk and calculates dynamic premiums` |
| **Model** | Claude 3 Sonnet |
| **Instructions** | See section 2.3 below |

#### 2.3 Agent Instructions (Copy & Paste)

```
You are an expert insurance underwriter and pricing specialist for the GTM Insurance platform.

Your role:
1. Analyze telemetry data and risk indicators from customers
2. Calculate appropriate insurance premiums based on risk profiles
3. Provide clear explanations of pricing decisions
4. Ensure compliance with rating guidelines

When a user asks about pricing:
1. Use the PricingSimulator tool to calculate a premium
2. Explain the factors affecting the price
3. Provide the recommended premium

Always:
- Be professional and consultative
- Back calculations with data
- Highlight key risk factors
- Suggest mitigation strategies when appropriate
```

Click **Create** to proceed.

### Step 3: Add Action Group (Lambda Integration)

After agent creation, you'll see **"Add action group"** button.

#### 3.1 Create Action Group

1. Click **Add action group**
2. Fill in:
   - **Action group name**: `PricingSimulator`
   - **Description**: `Calculates insurance premiums based on risk data`

#### 3.2 Configure Lambda Integration

1. Select: **Lambda function**
2. Choose Lambda: `GTM_insurance_dynamicpricing_ratingengine_Gateway`
3. For **Schema**:
   - Select: **Define with API schema**
   - Upload OpenAPI file: `DynamicPricing_Rating_engine/openapi.yaml`

#### 3.3 Test & Save

1. Click **Save**
2. You should see confirmation: "Action group added successfully"

### Step 4: Create Agent Alias

Aliases are required to run the agent.

1. Go to your **GTM-Dynamic-Pricing-Agent** page
2. Scroll down to **Aliases**
3. Click **Create alias**
   - **Name**: `production`
   - **Description**: `Production environment`
   - **Agent version**: Leave as default
4. Click **Create**

### Step 5: Configure Guardrails (Optional)

Guardrails provide safety controls:

1. On agent page, click **Guardrails** tab (if available)
2. Configure:
   - ✅ **Content filtering**: Block harmful content
   - ✅ **PII detection**: Detect SSN, credit card, email
   - ✅ **Topic blocking**: Block off-topic requests

Note: Bedrock Guardrails are in preview. If not available, configure in AWS Console > Bedrock > Guardrails separately.

### Step 6: Get Agent IDs

You need two IDs for testing:

1. Go to your agent page
2. Look for:
   - **Agent ID**: Copy this value (e.g., `A6N7J8C9K2X1`)
   - **Alias ID**: Copy from the Aliases section (usually `PROD` or similar)

## Running Tests

### Using Environment Variables

```bash
export BEDROCK_AGENT_ID=<YOUR_AGENT_ID>
export BEDROCK_AGENT_ALIAS=production
export AWS_REGION=ap-south-1

python3 bedrock-test-automation.py
```

### Using Command Line

```bash
python3 bedrock-test-automation.py \
  --agent-id <YOUR_AGENT_ID> \
  --alias production \
  --region ap-south-1
```

### Test Specific Layer

```bash
# Test only Think layer (agent reasoning)
python3 bedrock-test-automation.py --agent-id <ID> --layer think

# Test only Action layer (Lambda integration)
python3 bedrock-test-automation.py --agent-id <ID> --layer action

# Test Safety layer (guardrails)
python3 bedrock-test-automation.py --agent-id <ID> --layer safety

# Test end-to-end
python3 bedrock-test-automation.py --agent-id <ID> --layer e2e
```

## Troubleshooting

### "Invalid Agent ID" Error

**Problem**: Script says Agent ID is invalid

**Solution**:
1. Go to AWS Bedrock Console > Agents
2. Click your agent name
3. Look at the URL: `https://console.aws.amazon.com/bedrock/home?region=ap-south-1#/agents/XXXXX`
4. Copy the ID from the URL
5. Run: `python3 bedrock-test-automation.py --agent-id XXXXX`

### "Access Denied" Error

**Problem**: Can't invoke agent or Lambda

**Solution**:
1. Check IAM permissions: User must have:
   - `bedrock:InvokeAgent`
   - `lambda:InvokeFunction`
2. Verify Lambda trust relationship allows Bedrock
3. Run: `aws iam get-role --role-name bedrock-gtm-agent-role` to check role

### "Model Not Available" Error

**Problem**: Claude model not enabled

**Solution**:
1. Go to Bedrock Console > Models
2. Search for Claude 3
3. Click **Enable**
4. Wait a few minutes for activation
5. Try again

### Agent Not Responding

**Problem**: Agent calls return empty or timeout

**Solution**:
1. Verify Lambda function is working:
   ```bash
   aws lambda invoke --function-name GTM_insurance_dynamicpricing_ratingengine_Gateway \
     --payload '{"detail":{"riskScore":65,"basePremium":100000}}' \
     /tmp/response.json
   ```

2. Check Lambda logs:
   ```bash
   aws logs tail /aws/lambda/GTM_insurance_dynamicpricing_ratingengine_Gateway --follow
   ```

3. Verify DynamoDB tables exist:
   ```bash
   aws dynamodb list-tables | grep GTM
   ```

## Verification Checklist

After setup, verify by running:

```bash
# Set your Agent ID
export BEDROCK_AGENT_ID=<YOUR_ID>

# Test basic invoke
python3 bedrock-test-automation.py --layer think --region ap-south-1
```

Expected output:
```
✅ AWS clients initialized
   Agent ID: <YOUR_ID>
   Alias: production
   Region: ap-south-1

==================================================
LAYER 1: THINK LAYER - Agent Evaluation
==================================================

▶ Test: Risk Score 50 - High Risk...
```

## Cost Considerations

- **Agent Invocation**: ~$0.001 per invocation (varies by model)
- **Lambda Invocation**: ~$0.0000002 per invocation
- **Testing**: Approximately $0.10 per 100 test runs

Estimate: Running full test suite (50 tests) ≈ $0.05

## Next Steps

1. ✅ Create agent following steps above
2. ✅ Run `python3 bedrock-test-automation.py --agent-id <ID>`
3. ✅ Review test results in `bedrock-test-report-*.txt`
4. ✅ (Optional) Set up Bedrock Knowledge Base for RAG
5. ✅ Integrate into GTM demo pipeline

## Additional Resources

- [AWS Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Claude 3 Model Card](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-models.html)
- [OpenAPI Schema Format](https://spec.openapis.org/oas/v3.1.0)
- [Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)

---

**Last Updated**: 2024  
**Status**: Production Ready
