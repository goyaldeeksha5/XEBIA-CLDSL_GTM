output "orchestration_agent_function_name" {
  description = "Name of the Orchestration Agent Lambda function"
  value       = aws_lambda_function.orchestration_agent.function_name
}

output "extraction_agent_function_name" {
  description = "Name of the Extraction Agent Lambda function"
  value       = aws_lambda_function.extraction_agent.function_name
}

output "validation_agent_function_name" {
  description = "Name of the Validation Agent Lambda function"
  value       = aws_lambda_function.validation_agent.function_name
}

output "summary_agent_function_name" {
  description = "Name of the Summary Agent Lambda function"
  value       = aws_lambda_function.summary_agent.function_name
}

output "extraction_queue_url" {
  description = "URL of the Extraction Agent SQS queue"
  value       = aws_sqs_queue.extraction_queue.url
}

output "validation_queue_url" {
  description = "URL of the Validation Agent SQS queue"
  value       = aws_sqs_queue.validation_queue.url
}

output "summary_queue_url" {
  description = "URL of the Summary Agent SQS queue"
  value       = aws_sqs_queue.summary_queue.url
}

output "submissions_bucket_name" {
  description = "Name of the S3 bucket for submissions"
  value       = aws_s3_bucket.submissions_bucket.id
}

output "submissions_bucket_arn" {
  description = "ARN of the S3 bucket for submissions"
  value       = aws_s3_bucket.submissions_bucket.arn
}

output "notifications_topic_arn" {
  description = "ARN of the SNS topic for notifications"
  value       = aws_sns_topic.underwriting_notifications.arn
}

output "alerts_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.underwriting_alerts.arn
}

output "orchestration_role_arn" {
  description = "ARN of the Orchestration Agent IAM role"
  value       = aws_iam_role.orchestration_agent_role.arn
}

output "extraction_role_arn" {
  description = "ARN of the Extraction Agent IAM role"
  value       = aws_iam_role.extraction_agent_role.arn
}

output "validation_role_arn" {
  description = "ARN of the Validation Agent IAM role"
  value       = aws_iam_role.validation_agent_role.arn
}

output "summary_role_arn" {
  description = "ARN of the Summary Agent IAM role"
  value       = aws_iam_role.summary_agent_role.arn
}

output "orchestration_log_group" {
  description = "CloudWatch Log Group for Orchestration Agent"
  value       = aws_cloudwatch_log_group.orchestration_logs.name
}

output "extraction_log_group" {
  description = "CloudWatch Log Group for Extraction Agent"
  value       = aws_cloudwatch_log_group.extraction_logs.name
}

output "validation_log_group" {
  description = "CloudWatch Log Group for Validation Agent"
  value       = aws_cloudwatch_log_group.validation_logs.name
}

output "summary_log_group" {
  description = "CloudWatch Log Group for Summary Agent"
  value       = aws_cloudwatch_log_group.summary_logs.name
}
