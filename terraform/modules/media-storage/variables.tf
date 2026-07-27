variable "bucket_name" {
  description = "Globally unique name for the private media bucket."
  type        = string
}

variable "enable_versioning" {
  description = "Enable S3 object versioning. Disabled by default to minimize storage costs."
  type        = bool
  default     = false
}

variable "abort_incomplete_upload_days" {
  description = "Days before incomplete multipart uploads are removed."
  type        = number
  default     = 7
}

variable "noncurrent_version_expiration_days" {
  description = "Days before noncurrent object versions expire. Null disables the rule."
  type        = number
  default     = null
}

variable "tags" {
  description = "Tags applied to the bucket."
  type        = map(string)
  default     = {}
}
