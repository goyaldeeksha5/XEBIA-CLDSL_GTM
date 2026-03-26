# Bedrock Agent Quick Reference

## 30-Second Setup

```bash
# 1. Create agent in AWS Console (2 minutes)
# - Go to https://console.aws.amazon.com/bedrock
# - Agents > Create agent
# - Name: GTM-Dynamic-Pricing-Agent
# - Model: Claude 3 Sonnet
# - Add Action Group: GTM_insurance_dynamicpricing_ratingengine_Gateway
# - Create Alias: production
# - Copy Agent ID

# 2. Run tests
export BEDROCK_AGENT_ID=YOUR_AGENT_ID_HERE
python3 bedrock-test-automation.py
```

## Key IDs to Remember

| Item | Where to Find | Example |
|------|---------------|---------|
| **Agent ID** | AWS Console > Bedrock > Agents > Your Agent (in URL) | `A6N7J8C9K2X1` |
| **Agent Alias** | AWS Console > Bedrock > Agents > Your Agent > Aliases | `production` |
| **Lambda ARN** | AWS Console > Lambda > GTM_insurance_dynamicpricing_ratingengine_Gateway | `arn:aws:lambda:ap-south-1:474532148129:function:GTM_insurance_dynamicpricing_ratingengine_Gateway` |

## Common Commands

### Test Specific Layer
```bash
# Reasoning tests
python3 bedrock-test-automation.py --agent-id <ID> --layer think

# Lambda integration tests
python3 bedrock-test-automation.py --agent-id <ID> --layer action

# Safety/guardrails tests
python3 bedrock-test-automation.py --agent-id <ID> --layer safety

# Full simulation
python3 bedrock-test-automation.py --agent-id <ID> --layer e2e
```

### Verify Setup
```bash
# Check Lambda is working
aws lambda invoke \
  --function-name GTM_insurance_dynamicpricing_ratingengine_Gateway \
  --payload '{"detail":{"riskScore":65,"basePremium":100000}}' \
  /tmp/response.json && cat /tmp/response.json

# Check Lambda logs
aws logs tail /aws/lambda/GTM_insurance_dynamicpricing_ratingengine_Gateway --follow

# List Bedrock agents
aws bedrock list-agents --region ap-south-1
```

## Environment Variables

```bash
export BEDROCK_AGENT_ID=<YOUR_ID>
export BEDROCK_AGENT_ALIAS=production
export AWS_REGION=ap-south-1
```

## OpenAPI Schema Reference

**File**: `DynamicPricing_Rating_engine/openapi.yaml`

**Tool Name**: `submit_risk_assessment`

**Parameters**:
- `riskScore` (number): 0-100 risk assessment score
- `basePremium` (number): Base insurance premium in dollars
- `deviceId` (string): Unique device identifier
- `timestamp` (string): Event timestamp (ISO 8601)

**Example Response**:
```json
{
  "adjustedPremium": 143750,
  "multiplier": 1.15,
  "reasoning": "Score 58 indicates elevated risk, applying 1.15x multiplier"
}
```

## Test Layers

| Layer | Focus | Tests |
|-------|-------|-------|
| **THINK** | Agent reasoning & tool selection | 4 tests |
| **ACTION** | Lambda integration & schema | 3 tests |
| **SAFETY** | Guardrails & adversarial inputs | 4 tests |
| **E2E** | Complete workflow | 2 tests |

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Invalid Agent ID` | Copy actual ID from AWS Console > Bedrock > Agents |
| `Access Denied` | Check IAM permissions for bedrock:InvokeAgent |
| `Model not available` | Go to Bedrock Console > Models and enable Claude 3 |
| `Lambda timeout` | Increase Lambda timeout to 60s in AWS Console |
| `No response` | Check Lambda logs: `aws logs tail /aws/lambda/GTM_insurance_dynamicpricing_ratingengine_Gateway` |

## File Locations

```
/workspaces/XEBIA-CLDSL_GTM/
├── bedrock-test-automation.py      # Main test runner
├── bedrock-test-data.json          # Test scenarios
├── bedrock-agent.tf                # Terraform config (reference)
├── BEDROCK_SETUP_GUIDE.md          # Detailed setup
├── DynamicPricing_Rating_engine/
│   ├── openapi.yaml                # Action Group schema
│   └── index.py                    # Lambda handler
└── bedrock-test-report-*.txt       # Test results (auto-generated)
```

## Next: GTM Demo Integration

After setup, integrate agent into GTM presentation:

```python
import boto3

bedrock_runtime = boto3.client("bedrock-agent-runtime", region_name="ap-south-1")

response = bedrock_runtime.invoke_agent(
    agentId="<YOUR_AGENT_ID>",
    agentAliasId="production",
    sessionId="demo-session",
    inputText="What's the premium for a high-risk customer with score 45?"
)
```

---

**Need Help?** See `BEDROCK_SETUP_GUIDE.md` for detailed instructions
