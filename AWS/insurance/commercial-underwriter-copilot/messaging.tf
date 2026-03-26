# SQS Queue for Extraction Agent tasks
resource "aws_sqs_queue" "extraction_queue" {
  name                       = "${var.project_name}-extraction-queue"
  delay_seconds              = 0
  max_message_size           = 262144 # 256 KB
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20
  visibility_timeout_seconds = 1800 # 30 minutes
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.extraction_dlq.arn
    maxReceiveCount     = 3
  })

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
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.validation_dlq.arn
    maxReceiveCount     = 3
  })

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
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.summary_dlq.arn
    maxReceiveCount     = 3
  })

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



# SNS Topic for notifications
resource "aws_sns_topic" "underwriting_notifications" {
  name = "${var.project_name}-notifications"

  tags = {
    Name = "${var.project_name}-notifications"
  }
  lifecycle {
    ignore_changes = [tags]
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "underwriting_alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name = "${var.project_name}-alerts"
  }
  lifecycle {
   ignore_changes = [tags]
  }
}
