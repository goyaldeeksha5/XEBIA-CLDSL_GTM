# S3 Bucket for document submissions and data storage
resource "aws_s3_bucket" "submissions_bucket" {
  bucket = var.s3_submission_bucket != "" ? lower(replace(var.s3_submission_bucket, "_", "-")) : lower(replace("${var.project_name}-submissions-${data.aws_caller_identity.current.account_id}", "_", "-"))

  tags = {
    Name = "${var.project_name}-submissions"
  }
}

# Enable versioning for document tracking
resource "aws_s3_bucket_versioning" "submissions_versioning" {
  bucket = aws_s3_bucket.submissions_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access to submissions
resource "aws_s3_bucket_public_access_block" "submissions_block" {
  bucket = aws_s3_bucket.submissions_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "submissions_encryption" {
  bucket = aws_s3_bucket.submissions_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "submissions_lifecycle" {
  bucket = aws_s3_bucket.submissions_bucket.id

  rule {
    id     = "archive-old-documents"
    status = "Enabled"

    filter {
      prefix = "submissions/"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555 # 7 years
    }
  }

  rule {
    id     = "archive-processed-data"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# EventBridge Integration for document uploads
resource "aws_s3_bucket_notification" "submissions_bucket_notification" {
  bucket      = aws_s3_bucket.submissions_bucket.id
  eventbridge = true
}

# S3 folder prefixes are created via PUT operations; no explicit resources needed
