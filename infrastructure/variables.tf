variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Environment name (production, staging)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all resources"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "VPC CIDR"
}

variable "artifacts_bucket_name" {
  type        = string
  description = "S3 bucket name for PDF artifacts (globally unique)"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Master password (if set, manage_master_user_password should be false)"
}

variable "ecr_repositories" {
  type        = map(string)
  default     = null
  description = "Optional override for ECR repository suffixes (logical name => suffix). Defaults include migration, backend, frontend, data_ingestion."
  nullable    = true
}

variable "openai_api_key" {
  type        = string
  sensitive   = true
  description = "OpenAI API key for backend and ingestion workers"
}

variable "jwt_secret" {
  type        = string
  sensitive   = true
  description = "JWT signing secret for the API (SECRET_KEY)"
}

variable "frontend_url_override" {
  type        = string
  default     = null
  description = "Optional CORS origin override; leave null to use http://<public ALB DNS>"
  nullable    = true
}