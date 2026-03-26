output "telematics_table_name" {
  description = "DynamoDB telematics table name"
  value       = aws_dynamodb_table.gtm_telematics_table.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.gtm_logs.name
}

output "dynamodb_table_name" {
  description = "DynamoDB proposals table name"
  value       = aws_dynamodb_table.gtm_proposals.name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.gtm_agent_gateway.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.gtm_agent_gateway.function_name
}

output "eventbridge_rule_name" {
  description = "EventBridge rule name"
  value       = aws_cloudwatch_event_rule.gtm_risk_rule.name
}

output "iam_role_arn" {
  description = "IAM role ARN for Lambda"
  value       = aws_iam_role.gtm_lambda_role.arn
}
