# --- Terraform Configuration ---
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend Configuration for S3 State Storage
  backend "s3" {
    bucket         = "xebia-cldsl-gtm-terraform-state-474532148129"
    key            = "prod/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "xebia-cldsl-gtm-terraform-locks"
    encrypt        = true
  }
}

# --- AWS Provider Configuration ---
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "XEBIA-CLDSL-GTM"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
