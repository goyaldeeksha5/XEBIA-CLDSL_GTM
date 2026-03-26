# --- Root Module Main Configuration ---
# Deploys the Dynamic Pricing Rating Engine infrastructure

module "dynamic_pricing" {
  source = "./DynamicPricing_Rating_engine"

  aws_region     = var.aws_region
  project_name   = "GTM_insurance_dynamicpricing_ratingengine"
  environment    = var.environment
}

