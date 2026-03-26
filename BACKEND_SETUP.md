# Backend Configuration Setup Guide

## Overview
This Terraform configuration uses AWS S3 for remote state storage with DynamoDB for state locking.

## S3 Bucket and Backend Information

### Bucket Name
The S3 bucket name is generated using the `aws_account_id` variable: `xebia-cldsl-gtm-terraform-state-${aws_account_id}`

Current value: `xebia-cldsl-gtm-terraform-state-474532148129`

### Bucket Features
- ✅ Versioning enabled for state file history
- ✅ Server-side encryption (AES256)
- ✅ Public access blocked for security
- ✅ DynamoDB table for state locking

### DynamoDB Lock Table
- **Table Name**: `xebia-cldsl-gtm-terraform-locks`
- **Key**: `LockID`
- **Billing**: Pay-per-request

## Setup Instructions

### Step 1: Initialize Terraform with Backend Configuration

```bash
terraform init
```

The backend is now configured with your AWS account ID (474532148129).

### Step 1a: To Change the Account ID

Edit [variables.tf](variables.tf) and change the `aws_account_id` variable default value:

```hcl
variable "aws_account_id" {
  description = "AWS Account ID for backend state bucket"
  type        = string
  default     = "YOUR_NEW_ACCOUNT_ID"  # Change this value
}
```

Then also update [backend-config.hcl](backend-config.hcl) with the new bucket name.

### Step 2: Verify Backend Configuration
```bash
terraform backend show
```

## Configuration Variables

The following variables can be modified to customize the backend setup:

```hcl
# From variables.tf
aws_account_id = "474532148129"  # Change this to use a different AWS account
```

To use a different account ID, update the `aws_account_id` variable in [variables.tf](variables.tf#L8-L11).

## Files Overview

- **backend.tf**: Defines S3 bucket and DynamoDB table for state storage (uses `aws_account_id` variable)
- **provider.tf**: AWS provider configuration and backend specification
- **variables.tf**: Input variables including `aws_account_id` for the backend bucket name
- **backend-config.hcl**: Backend configuration file for init command
- **main.tf**: Root module entry point
- **DynamicPricing_Rating_engine/main.tf**: Infrastructure resources

## Important Notes

1. **First Run**: The S3 bucket and DynamoDB table must be created before referencing them in the backend configuration
2. **Bucket Naming**: AWS requires globally unique bucket names, so we use the account ID as a suffix
3. **State Locking**: DynamoDB prevents concurrent modifications to the state file
4. **Encryption**: All state files are encrypted at rest using AES256

## Troubleshooting

### If backend initialization fails:
1. Ensure AWS credentials are configured: `aws configure`
2. Verify IAM permissions for S3 and DynamoDB operations
3. Check that your AWS account ID is correct

### To migrate existing state:
```bash
terraform state push <local_state_file>
```

## Security Best Practices

- ✅ State files are encrypted
- ✅ Public access is blocked
- ✅ Versioning is enabled for recovery
- ✅ Use IAM roles for automated access
- ✅ Enable CloudTrail for audit logging
