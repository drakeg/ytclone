output "bucket_name" {
  description = "Name of the private media bucket."
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "ARN of the private media bucket."
  value       = aws_s3_bucket.this.arn
}

output "regional_domain_name" {
  description = "Regional S3 domain name for future CloudFront integration."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}
