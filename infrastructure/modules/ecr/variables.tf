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

variable "repositories" {
  type        = map(string)
  description = "Map of logical name => ECR repository name suffix (full name: {project}-{suffix}-{environment})"
  default = {
    migration      = "ecr-migration-repo"
    backend        = "backend"
    frontend       = "frontend"
    data_ingestion = "data-ingestion"
  }
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
