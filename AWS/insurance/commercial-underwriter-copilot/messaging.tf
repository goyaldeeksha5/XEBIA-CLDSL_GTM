# SQS Queue for Extraction Agent tasks
resource "aws_sqs_queue" "extraction_queue" {
  name                       = "${var.project_name}-extraction-queue"
  delay_seconds              = 0
  max_message_size           = 262144 # 256 KB
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 1800 # 30 minutes

  tags = {
    Name = "${var.project_name}-extraction-queue"
  }
}

# SQS Queue for Validation Agent tasks
resource "aws_sqs_queue" "validation_queue" {
  name                       = "${var.project_name}-validation-queue"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 1800

  tags = {
    Name = "${var.project_name}-validation-queue"
  }
}

# SQS Queue for Summary Agent tasks
resource "aws_sqs_queue" "summary_queue" {
  name                       = "${var.project_name}-summary-queue"
  delay_seconds              = 0
  max_message_size           = 262144
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 1800

  tags = {
    Name = "${var.project_name}-summary-queue"
  }
}

# DLQ for Extraction Agent
resource "aws_sqs_queue" "extraction_dlq" {
  name                      = "${var.project_name}-extraction-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "${var.project_name}-extraction-dlq"
  }
}

# DLQ for Validation Agent
resource "aws_sqs_queue" "validation_dlq" {
  name                      = "${var.project_name}-validation-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "${var.project_name}-validation-dlq"
  }
}

# DLQ for Summary Agent
resource "aws_sqs_queue" "summary_dlq" {
  name                      = "${var.project_name}-summary-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "${var.project_name}-summary-dlq"
  }
}

# Dead Letter Queue policy for Extraction
resource "aws_sqs_queue_redrive_policy" "extraction_queue_dlq" {
  queue_url           = aws_sqs_queue.extraction_queue.id
  dead_letter_target_arn = aws_sqs_queue.extraction_dlq.arn
  max_receive_count   = 3
}

# Dead Letter Queue policy for Validation
resource "aws_sqs_queue_redrive_policy" "validation_queue_dlq" {
  queue_url           = aws_sqs_queue.validation_queue.id
  dead_letter_target_arn = aws_sqs_queue.validation_dlq.arn
  max_receive_count   = 3
}

# Dead Letter Queue policy for Summary
resource "aws_sqs_queue_redrive_policy" "summary_queue_dlq" {
  queue_url           = aws_sqs_queue.summary_queue.id
  dead_letter_target_arn = aws_sqs_queue.summary_dlq.arn
  max_receive_count   = 3
}

# SNS Topic for notifications
resource "aws_sns_topic" "underwriting_notifications" {
  name = "${var.project_name}-notifications"

  tags = {
    Name = "${var.project_name}-notifications"
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "underwriting_alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name = "${var.project_name}-alerts"
  }
}
