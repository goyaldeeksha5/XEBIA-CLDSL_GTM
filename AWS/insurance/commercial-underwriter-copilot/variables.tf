variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "GTM_underwriter_copilot"
}

variable "s3_submission_bucket" {
  description = "S3 bucket for incoming submissions"
  type        = string
  default     = ""
}

variable "submission_prefix" {
  description = "S3 prefix for submission documents"
  type        = string
  default     = "submissions/"
}

variable "historical_data_prefix" {
  description = "S3 prefix for historical loss data"
  type        = string
  default     = "historical-data/"
}

variable "appetite_guide_prefix" {
  description = "S3 prefix for underwriting appetite guides"
  type        = string
  default     = "appetite-guides/"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for reasoning"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "sagemaker_endpoint" {
  description = "SageMaker risk scoring endpoint name"
  type        = string
  default     = ""
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory" {
  description = "Lambda function memory allocation in MB"
  type        = number
  default     = 512
}

variable "agents_count" {
  description = "Number of agent workers"
  type        = number
  default     = 3
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_api_gateway" {
  description = "Enable API Gateway for AgentCore API"
  type        = bool
  default     = true
}

variable "api_domain" {
  description = "Custom domain name for API (e.g., api.underwriter.company.com)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = ""
}
