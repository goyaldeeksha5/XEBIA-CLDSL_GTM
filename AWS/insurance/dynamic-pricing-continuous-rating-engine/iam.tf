# --- IAM Policies for Lambda ---
resource "aws_iam_role_policy" "gtm_lambda_dynamodb_policy" {
  name   = "${var.project_name}_DynamoDB_Policy"
  role   = aws_iam_role.gtm_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.gtm_proposals.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "gtm_lambda_telematics_policy" {
  name   = "${var.project_name}_Telematics_Policy"
  role   = aws_iam_role.gtm_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.gtm_telematics_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "gtm_lambda_logs_policy" {
  name   = "${var.project_name}_Logs_Policy"
  role   = aws_iam_role.gtm_lambda_role.id
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
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${var.project_name}*"
      }
    ]
  })
}
