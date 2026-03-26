# Orchestration Agent Lambda Function
resource "aws_lambda_function" "orchestration_agent" {
  filename            = "lambda_functions/build/orchestration_agent.zip"
  function_name       = "${var.project_name}-orchestration-agent"
  role                = aws_iam_role.orchestration_agent_role.arn
  handler             = "index.handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory

  environment {
    variables = {
      EXTRACTION_QUEUE_URL  = aws_sqs_queue.extraction_queue.url
      VALIDATION_QUEUE_URL  = aws_sqs_queue.validation_queue.url
      SUMMARY_QUEUE_URL     = aws_sqs_queue.summary_queue.url
      S3_BUCKET            = aws_s3_bucket.submissions_bucket.id
      SNS_TOPIC_ARN        = aws_sns_topic.underwriting_notifications.arn
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      ENVIRONMENT          = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy.agent_messaging_policy_orchestration,
    aws_iam_role_policy.cloudwatch_logs_policy_orchestration
  ]

  tags = {
    Name = "${var.project_name}-orchestration-agent"
  }
}

# Extraction Agent Lambda Function
resource "aws_lambda_function" "extraction_agent" {
  filename            = "lambda_functions/build/extraction_agent.zip"
  function_name       = "${var.project_name}-extraction-agent"
  role                = aws_iam_role.extraction_agent_role.arn
  handler             = "index.handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory

  environment {
    variables = {
      S3_BUCKET            = aws_s3_bucket.submissions_bucket.id
      VALIDATION_QUEUE_URL = aws_sqs_queue.validation_queue.url
      HISTORY_PREFIX       = var.historical_data_prefix
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      ENVIRONMENT          = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy.extraction_agent_textract_policy,
    aws_iam_role_policy.agent_messaging_policy_extraction,
    aws_iam_role_policy.cloudwatch_logs_policy_extraction
  ]

  tags = {
    Name = "${var.project_name}-extraction-agent"
  }
}

# Validation Agent Lambda Function
resource "aws_lambda_function" "validation_agent" {
  filename            = "lambda_functions/build/validation_agent.zip"
  function_name       = "${var.project_name}-validation-agent"
  role                = aws_iam_role.validation_agent_role.arn
  handler             = "index.handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory

  environment {
    variables = {
      S3_BUCKET            = aws_s3_bucket.submissions_bucket.id
      APPETITE_PREFIX      = var.appetite_guide_prefix
      SUMMARY_QUEUE_URL    = aws_sqs_queue.summary_queue.url
      SAGEMAKER_ENDPOINT   = var.sagemaker_endpoint
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      ENVIRONMENT          = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy.validation_sagemaker_policy,
    aws_iam_role_policy.agent_messaging_policy_validation,
    aws_iam_role_policy.cloudwatch_logs_policy_validation
  ]

  tags = {
    Name = "${var.project_name}-validation-agent"
  }
}

# Summary Agent Lambda Function
resource "aws_lambda_function" "summary_agent" {
  filename            = "lambda_functions/build/summary_agent.zip"
  function_name       = "${var.project_name}-summary-agent"
  role                = aws_iam_role.summary_agent_role.arn
  handler             = "index.handler"
  runtime             = "python3.11"
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory

  environment {
    variables = {
      S3_BUCKET        = aws_s3_bucket.submissions_bucket.id
      SNS_TOPIC_ARN    = aws_sns_topic.underwriting_notifications.arn
      BEDROCK_MODEL_ID = var.bedrock_model_id
      ENVIRONMENT      = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy.agent_messaging_policy_summary,
    aws_iam_role_policy.cloudwatch_logs_policy_summary
  ]

  tags = {
    Name = "${var.project_name}-summary-agent"
  }
}

# Event Source Mapping for Extraction Queue
resource "aws_lambda_event_source_mapping" "extraction_queue_mapping" {
  event_source_arn = aws_sqs_queue.extraction_queue.arn
  function_name    = aws_lambda_function.extraction_agent.function_name
  batch_size       = 1
  enabled          = true
}

# Event Source Mapping for Validation Queue
resource "aws_lambda_event_source_mapping" "validation_queue_mapping" {
  event_source_arn = aws_sqs_queue.validation_queue.arn
  function_name    = aws_lambda_function.validation_agent.function_name
  batch_size       = 1
  enabled          = true
}

# Event Source Mapping for Summary Queue
resource "aws_lambda_event_source_mapping" "summary_queue_mapping" {
  event_source_arn = aws_sqs_queue.summary_queue.arn
  function_name    = aws_lambda_function.summary_agent.function_name
  batch_size       = 1
  enabled          = true
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "orchestration_logs" {
  name              = "/aws/lambda/${var.project_name}-orchestration-agent"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-orchestration-logs"
  }
}

resource "aws_cloudwatch_log_group" "extraction_logs" {
  name              = "/aws/lambda/${var.project_name}-extraction-agent"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-extraction-logs"
  }
}

resource "aws_cloudwatch_log_group" "validation_logs" {
  name              = "/aws/lambda/${var.project_name}-validation-agent"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-validation-logs"
  }
}

resource "aws_cloudwatch_log_group" "summary_logs" {
  name              = "/aws/lambda/${var.project_name}-summary-agent"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-summary-logs"
  }
}
