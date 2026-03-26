# Backend configuration file for Terraform
# Use with: terraform init -backend-config=backend-config.hcl
# Or update bucket name dynamically by modifying aws_account_id variable

bucket         = "xebia-cldsl-gtm-terraform-state-474532148129"
key            = "prod/terraform.tfstate"
region         = "ap-south-1"
dynamodb_table = "xebia-cldsl-gtm-terraform-locks"
encrypt        = true
