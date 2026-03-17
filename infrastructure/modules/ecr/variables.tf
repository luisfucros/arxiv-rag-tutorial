variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Environment name (production, staging)"
}

variable "repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "ecr-migration-repo"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
