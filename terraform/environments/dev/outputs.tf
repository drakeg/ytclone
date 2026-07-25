output "media_bucket_name" {
  description = "Name of the private S3 media bucket."
  value       = module.media_storage.bucket_name
}

output "media_bucket_arn" {
  description = "ARN of the private S3 media bucket."
  value       = module.media_storage.bucket_arn
}

output "budget_name" {
  description = "Name of the monthly AWS cost budget."
  value       = module.budget.budget_name
}
