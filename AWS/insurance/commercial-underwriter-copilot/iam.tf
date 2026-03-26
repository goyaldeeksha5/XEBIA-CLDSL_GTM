# IAM Role for Orchestration Agent
resource "aws_iam_role" "orchestration_agent_role" {
  name = "${var.project_name}-orchestration-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role for Extraction Agent
resource "aws_iam_role" "extraction_agent_role" {
  name = "${var.project_name}-extraction-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role for Validation Agent
resource "aws_iam_role" "validation_agent_role" {
  name = "${var.project_name}-validation-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role for Summary Agent
resource "aws_iam_role" "summary_agent_role" {
  name = "${var.project_name}-summary-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Policy for Textract access (Extraction Agent)
resource "aws_iam_role_policy" "extraction_agent_textract_policy" {
  name   = "${var.project_name}-extraction-textract-policy"
  role   = aws_iam_role.extraction_agent_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:AnalyzeDocument",
          "textract:GetDocumentAnalysis",
          "textract:StartDocumentAnalysis"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for S3 access (all agents)
resource "aws_iam_role_policy" "s3_access_policy" {
  for_each = toset([
    aws_iam_role.orchestration_agent_role.id,
    aws_iam_role.extraction_agent_role.id,
    aws_iam_role.validation_agent_role.id,
    aws_iam_role.summary_agent_role.id
  ])

  name   = "${var.project_name}-s3-access-policy"
  role   = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:GetObjectVersion"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_submission_bucket}",
          "arn:aws:s3:::${var.s3_submission_bucket}/*"
        ]
      }
    ]
  })
}

# Policy for Bedrock access (all agents)
resource "aws_iam_role_policy" "bedrock_access_policy" {
  for_each = toset([
    aws_iam_role.orchestration_agent_role.id,
    aws_iam_role.extraction_agent_role.id,
    aws_iam_role.validation_agent_role.id,
    aws_iam_role.summary_agent_role.id
  ])

  name   = "${var.project_name}-bedrock-access-policy"
  role   = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock-runtime:InvokeModel",
          "bedrock-runtime:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::model/${var.bedrock_model_id}"
      }
    ]
  })
}

# Policy for SageMaker access (Validation Agent)
resource "aws_iam_role_policy" "validation_sagemaker_policy" {
  name   = "${var.project_name}-validation-sagemaker-policy"
  role   = aws_iam_role.validation_agent_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "arn:aws:sagemaker:${var.aws_region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.sagemaker_endpoint}"
      }
    ]
  })
}

# Policy for Glue access (Data normalization)
resource "aws_iam_role_policy" "glue_access_policy" {
  for_each = toset([
    aws_iam_role.extraction_agent_role.id,
    aws_iam_role.validation_agent_role.id
  ])

  name   = "${var.project_name}-glue-access-policy"
  role   = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:UpdatePartition"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs_policy" {
  for_each = toset([
    aws_iam_role.orchestration_agent_role.id,
    aws_iam_role.extraction_agent_role.id,
    aws_iam_role.validation_agent_role.id,
    aws_iam_role.summary_agent_role.id
  ])

  name   = "${var.project_name}-cloudwatch-logs-policy"
  role   = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-*"
      }
    ]
  })
}

# Policy for inter-agent communication (SQS/SNS)
resource "aws_iam_role_policy" "agent_messaging_policy" {
  for_each = toset([
    aws_iam_role.orchestration_agent_role.id,
    aws_iam_role.extraction_agent_role.id,
    aws_iam_role.validation_agent_role.id,
    aws_iam_role.summary_agent_role.id
  ])

  name   = "${var.project_name}-agent-messaging-policy"
  role   = each.value
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.project_name}-*"
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  for_each = toset([
    aws_iam_role.orchestration_agent_role.arn,
    aws_iam_role.extraction_agent_role.arn,
    aws_iam_role.validation_agent_role.arn,
    aws_iam_role.summary_agent_role.arn
  ])

  role       = split("/", each.value)[1]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
