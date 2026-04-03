output "repository_urls" {
  value       = { for k, r in aws_ecr_repository.this : k => r.repository_url }
  description = "ECR repository URLs by logical name"
}

output "repository_url" {
  value       = aws_ecr_repository.this["migration"].repository_url
  description = "Migration ECR URL (backward compatibility)"
}

output "repository_name" {
  value       = aws_ecr_repository.this["migration"].name
  description = "Migration repository name (backward compatibility)"
}
