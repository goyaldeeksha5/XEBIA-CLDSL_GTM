# ⚠️ NOTE: Bedrock Agent terraform support is limited in AWS provider v5.0
# For full Bedrock Agent setup, use AWS Console or Bedrock API directly
# 
# To deploy Bedrock Agent manually:
# 1. Go to AWS Bedrock Console > Agents
# 2. Create Agent with these settings:
#    - Name: GTM-Dynamic-Pricing-Agent
#    - Model: Claude 3 Sonnet
#    - Instructions: (see BEDROCK_TESTING_GUIDE.md)
#
# 3. Add Action Group:
#    - Name: PricingSimulator
#    - Lambda: GTM_insurance_dynamicpricing_ratingengine_Gateway
#    - Schema: (see DynamicPricing_Rating_engine/openapi.yaml)
#
# 4. Add Guardrails:
#    - Enable content filtering
#    - Configure PII detection
#
# Once created, use Bedrock Console to get Agent ID and Alias ID
# Then run: python3 bedrock-test-automation.py --agent-id <YOUR_ID>

# Local reference for agent configuration
locals {
  bedrock_agent_config = {
    name        = "GTM-Dynamic-Pricing-Agent"
    model       = "anthropic.claude-3-sonnet-20240229-v1:0"
    description = "Agentic Rating Engine for Dynamic Insurance Pricing"
    
    system_prompt = <<-EOF
You are an advanced Insurance Pricing Agent for XEBIA's Dynamic Rating Engine.

## Your Role:
1. **THINK**: Analyze risk signals (telematics scores, market conditions)
2. **SENSE**: Retrieve actuarial guidelines
3. **ACT**: Invoke pricing simulation tool
4. **RESPOND**: Explain decisions with benchmarking

## Guidelines:
- Cite telematics score and risk multiplier
- Maintain rate adjustments within ±15%
- Provide market positioning context
- Flag proposals exceeding thresholds

## Constraints:
- Do NOT reveal competitor pricing
- Do NOT adjust based on demographics
- Do NOT propose discounts >5% without approval
- Respond ONLY to insurance queries
EOF
  }
}

# ===== IAM ROLES (for future use) =====

# IAM Role for Bedrock Agent (when deployed via Console)
resource "aws_iam_role" "bedrock_agent_role" {
  name = "bedrock-gtm-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name   = "bedrock-agent-policy"
  role   = aws_iam_role.bedrock_agent_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
          "bedrock:InvokeModel",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Role for Knowledge Base (when deployed via Console)
resource "aws_iam_role" "bedrock_kb_role" {
  name = "bedrock-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
    }]
  })
}

# ===== OUTPUTS =====

output "bedrock_setup_instructions" {
  value = <<-EOF
To set up Bedrock Agent manually:

1. Go to AWS Bedrock Console > Agents
2. Create Agent:
   - Name: GTM-Dynamic-Pricing-Agent
   - Model: Claude 3 Sonnet
   - Instructions: (see BEDROCK_TESTING_GUIDE.md)

3. Add Action Group:
   - Name: PricingSimulator
   - Lambda: GTM_insurance_dynamicpricing_ratingengine_Gateway
   - Schema: DynamicPricing_Rating_engine/openapi.yaml

4. Create Agent Alias:
   - Name: production

5. Enable Guardrails (AWS Console):
   - Content filtering
   - PII detection (SSN, customer data)
   - Off-topic blocking

After setup, get Agent ID and run:
python3 bedrock-test-automation.py --agent-id <YOUR_ID> --region ap-south-1
EOF

  description = "Manual setup instructions for Bedrock Agent"
}

output "bedrock_agent_iam_role_arn" {
  value       = aws_iam_role.bedrock_agent_role.arn
  description = "IAM role ARN for Bedrock Agent (use in Console)"
}

