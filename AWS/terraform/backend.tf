# --- S3 Bucket for Terraform State ---
resource "aws_s3_bucket" "terraform_state" {
  bucket = "xebia-cldsl-gtm-terraform-state-${var.aws_account_id}"

  tags = {
    Name        = "Terraform State Bucket"
    Environment = "Production"
    Project     = "XEBIA-CLDSL-GTM"
  }
}

# --- Enable Versioning for State Bucket ---
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Block Public Access to State Bucket ---
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Enable Server-Side Encryption ---
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- Enable MFA Delete Protection ---
resource "aws_s3_bucket_versioning" "terraform_state_mfa" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status     = "Enabled"
    mfa_delete = "Disabled"  # Change to "Enabled" if you have MFA device
  }
}

# --- DynamoDB Table for State Locking ---
resource "aws_dynamodb_table" "terraform_locks" {
  name             = "xebia-cldsl-gtm-terraform-locks"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Lock Table"
    Environment = "Production"
    Project     = "XEBIA-CLDSL-GTM"
  }
}

# --- Data Source for AWS Account ID ---
data "aws_caller_identity" "current" {}

# --- Outputs ---
output "terraform_state_bucket" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_lock_table" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.id
}
