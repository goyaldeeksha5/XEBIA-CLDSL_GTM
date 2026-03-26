# --- 1. Data Stream Layer (DynamoDB + CloudWatch Metrics) ---

# DynamoDB table for storing telematics data with timestamps
resource "aws_dynamodb_table" "gtm_telematics_table" {
  name           = "${var.project_name}_Telematics"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "DeviceID"
  range_key      = "Timestamp"

  attribute {
    name = "DeviceID"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "N"
  }

  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = {
    Name        = "GTM Telematics Table"
    Environment = var.environment
  }
}

# CloudWatch Log Group for Lambda and telematics monitoring
resource "aws_cloudwatch_log_group" "gtm_logs" {
  name              = "/aws/gtm/${var.project_name}"
  retention_in_days = 30

  tags = {
    Name        = "GTM Logs"
    Environment = var.environment
  }
}

# --- 2. State & Approval Layer (DynamoDB) ---
resource "aws_dynamodb_table" "gtm_proposals" {
  name         = "${var.project_name}_Proposals"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ProposalID"

  attribute {
    name = "ProposalID"
    type = "S"
  }

  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  tags = {
    Name        = "GTM Proposals Table"
    Environment = var.environment
  }
}

# --- 3. Execution Layer (Lambda) ---
# Note: Create lambda_function_payload.zip in this directory with your Lambda code
resource "aws_lambda_function" "gtm_agent_gateway" {
  filename      = "${path.module}/lambda_function_payload.zip"
  function_name = "${var.project_name}_Gateway"
  role          = aws_iam_role.gtm_lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout

  environment {
    variables = {
      PROPOSAL_TABLE   = aws_dynamodb_table.gtm_proposals.name
      TELEMATICS_TABLE = aws_dynamodb_table.gtm_telematics_table.name
      LOG_GROUP_NAME   = aws_cloudwatch_log_group.gtm_logs.name
    }
  }

  tags = {
    Name        = "GTM Agent Gateway"
    Environment = var.environment
  }
}

# --- 4. Orchestration Layer (EventBridge) ---
resource "aws_cloudwatch_event_rule" "gtm_risk_rule" {
  name        = "${var.project_name}_RiskSignal"
  description = "Triggers AgentCore on weather or competitor shifts"
  event_pattern = jsonencode({
    "source" : ["gtm.insurance.signals"],
    "detail-type" : ["RiskAnomalyDetected", "CompetitorShift"],
    "detail" : { "severity" : ["HIGH", "CRITICAL"] }
  })

  tags = {
    Name        = "GTM Risk Signal Rule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "gtm_trigger_target" {
  rule      = aws_cloudwatch_event_rule.gtm_risk_rule.name
  target_id = "TriggerAgentCore"
  arn       = aws_lambda_function.gtm_agent_gateway.arn
}

# --- 5. Permissions & IAM ---
resource "aws_lambda_permission" "gtm_allow_events" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gtm_agent_gateway.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.gtm_risk_rule.arn
}

resource "aws_iam_role" "gtm_lambda_role" {
  name               = "${var.project_name}_LambdaRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "GTM Lambda Role"
    Environment = var.environment
  }
}