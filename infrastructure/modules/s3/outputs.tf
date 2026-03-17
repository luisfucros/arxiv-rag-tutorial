output "artifacts_bucket_id" {
  value       = aws_s3_bucket.artifacts.id
  description = "S3 bucket ID for artifacts"
}

output "artifacts_bucket_arn" {
  value       = aws_s3_bucket.artifacts.arn
  description = "S3 bucket ARN for IAM policies"
}
