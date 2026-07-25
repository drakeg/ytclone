variable "aws_region" {
  description = "AWS region for regional resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project tag value used for naming and cost allocation."
  type        = string
  default     = "ytclone"
}

variable "media_bucket_name" {
  description = "Globally unique S3 bucket name for uploaded media."
  type        = string
}

variable "enable_media_versioning" {
  description = "Enable S3 versioning for media. Disabled by default to minimize cost."
  type        = bool
  default     = false
}

variable "monthly_budget_usd" {
  description = "Monthly AWS budget limit in US dollars."
  type        = number
  default     = 15
}

variable "budget_notification_emails" {
  description = "Email addresses that receive actual and forecast budget alerts."
  type        = list(string)
}
