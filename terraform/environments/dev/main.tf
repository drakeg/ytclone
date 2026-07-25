locals {
  common_tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

module "media_storage" {
  source = "../../modules/media-storage"

  bucket_name       = var.media_bucket_name
  enable_versioning = var.enable_media_versioning
  tags              = local.common_tags
}

module "budget" {
  source = "../../modules/budget"

  name                = "${var.project_name}-dev-monthly"
  monthly_limit_usd   = var.monthly_budget_usd
  notification_emails = var.budget_notification_emails
  project_tag_value   = var.project_name
}
