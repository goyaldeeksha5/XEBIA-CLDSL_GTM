# Bedrock Agent for Dynamic Pricing Rating Engine
# This agent orchestrates the pricing simulation workflow

resource "aws_bedrockagent_agent" "gtm_rating_agent" {
  agent_name             = "GTM-Dynamic-Pricing-Agent"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  idle_session_ttl_in_seconds = 900
  foundation_model       = "anthropic.claude-3-sonnet-20240229-v1:0"

  instruction = <<-EOF
You are an advanced Insurance Pricing Agent for XEBIA's Dynamic Rating Engine. Your role is to:

1. **THINK**: Analyze risk signals in real-time (telematics scores, market conditions)
2. **SENSE**: Retrieve actuarial guidelines from the knowledge base
3. **ACT**: Invoke the Lambda simulation tool to calculate dynamic premiums
4. **RESPOND**: Explain pricing decisions with market benchmarking

## Guidelines:
- Always cite the telematics score and risk multiplier in your recommendations
- Maintain rate adjustments within ±15% of the baseline premium
- Provide market positioning context (vs. $132,000 average)
- Flag any proposals exceeding risk thresholds for manual review

## Constraints:
- Do NOT reveal competitor pricing details that weren't provided
- Do NOT adjust rates based on customer demographics (compliance)
- Do NOT propose discounts > 5% without actuarial approval
- Respond ONLY to insurance-related queries

Respond conversationally but with technical precision.
EOF

  agent_type = "ORCHESTRATOR"
  
  tags = {
    Project     = "GTM Dynamic Pricing"
    Environment = "production"
  }
}

# Agent Alias for production deployment
resource "aws_bedrockagent_agent_alias" "gtm_rating_agent_prod" {
  agent_id      = aws_bedrockagent_agent.gtm_rating_agent.id
  agent_alias_name = "production"
  description   = "Production agent for live pricing simulations"
}

# Action Group: Link Lambda function as a tool
resource "aws_bedrockagent_agent_action_group" "simulate_pricing" {
  agent_id           = aws_bedrockagent_agent.gtm_rating_agent.id
  action_group_name  = "PricingSimulator"
  description        = "Simulates dynamic pricing based on risk signals"
  action_group_executor_type = "LAMBDA"

  function_schema {
    lambda_arn = aws_lambda_function.gtm_agent_gateway.arn
  }

  api_schema {
    s3_arn = aws_s3_object.openapi_schema.arn
  }
}

# KnowledgeBase for actuarial guidelines (optional but recommended)
resource "aws_bedrockagent_knowledge_base" "actuarial_guidelines" {
  name               = "GTM-Actuarial-Guidelines"
  role_arn           = aws_iam_role.bedrock_kb_role.arn
  knowledge_base_type = "VECTOR_RDS"

  storage_configuration {
    rds_configuration {
      credentials_secret_arn = aws_secretsmanager_secret.rds_credentials.arn
      database_name          = "actuarial_db"
      table_name             = "guidelines"
      resource_field         = "content"
    }
  }

  tags = {
    Project = "GTM Dynamic Pricing"
  }
}

# Bedrock Guardrails for compliance
resource "aws_bedrockguardrail" "insurance_compliance" {
  name                      = "GTM-Insurance-Guardrail"
  description               = "Ensures compliance and prevents prompt injection"
  blocked_input_messaging   = "I can only assist with insurance pricing queries."
  blocked_output_messaging  = "I cannot provide that information."

  sensitive_information_policy {
    pii_entities_config {
      actions = ["BLOCK", "ANONYMIZE"]
      
      regex_configs {
        name    = "SSN"
        pattern = "\\d{3}-\\d{2}-\\d{4}"
        action  = "ANONYMIZE"
      }

      regex_configs {
        name    = "PolicyNumber"
        pattern = "[A-Z]{3}-\\d{3}-[A-Z]{3}-\\d{4}"
        action  = "BLOCK"
      }
    }
  }

  topic_policy {
    topics_config {
      name      = "InsurancePricing"
      type      = "ALLOWED"
      examples  = ["Calculate premium", "What is the risk score?", "Show rate adjustment"]
    }

    topics_config {
      name      = "OffTopic"
      type      = "DENIED"
      examples  = ["Tell a joke", "What's the weather?", "Sports updates"]
    }

    topics_config {
      name      = "PII"
      type      = "DENIED"
      examples  = ["Customer list", "Policy holder names", "Social security numbers"]
    }
  }

  content_policy {
    filters_config {
      type       = "PROFANITY"
      input_strength  = "MEDIUM"
      output_strength = "MEDIUM"
    }

    filters_config {
      type       = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
  }

  word_policy {
    managed_word_lists_config {
      type = "PROFANITY"
    }
  }

  tags = {
    Project     = "GTM Dynamic Pricing"
    Compliance  = "Insurance Regulatory"
  }
}

# Attach Guardrail to Agent
resource "aws_bedrockagent_agent_guardrail_configuration" "gtm_safety" {
  agent_id              = aws_bedrockagent_agent.gtm_rating_agent.id
  guardrail_identifier  = aws_bedrockguardrail.insurance_compliance.id
  guardrail_version     = "1"
}

# IAM Role for Bedrock Agent
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
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.openapi_schema.arn}/*"
      }
    ]
  })
}

# IAM Role for Knowledge Base
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

# Outputs
output "bedrock_agent_id" {
  value       = aws_bedrockagent_agent.gtm_rating_agent.id
  description = "Bedrock Agent ID for API calls"
}

output "bedrock_agent_alias_id" {
  value       = aws_bedrockagent_agent_alias.gtm_rating_agent_prod.id
  description = "Bedrock Agent Alias for production"
}

output "guardrail_id" {
  value       = aws_bedrockguardrail.insurance_compliance.id
  description = "Guardrail ID for safety controls"
}
