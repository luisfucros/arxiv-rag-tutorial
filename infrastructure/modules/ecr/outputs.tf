output "repository_name" {
  value       = aws_ecr_repository.migration.name
  description = "ECR repository name"
}

output "repository_url" {
  value       = aws_ecr_repository.migration.repository_url
  description = "ECR repository URL"
}