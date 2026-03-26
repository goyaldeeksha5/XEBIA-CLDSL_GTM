# --- AWS Configuration Variables ---
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "XEBIA-CLDSL-GTM"
}

variable "aws_account_id" {
  description = "AWS Account ID for backend state bucket"
  type        = string
  default     = "474532148129"
}
