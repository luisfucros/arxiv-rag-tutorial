variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS tasks"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for ECS tasks"
}

variable "db_password" {
  type        = string
  default     = "rag_password"
  sensitive   = true
  description = "Master password (if set, manage_master_user_password should be false)"
}

variable "db_endpoint" {
  type        = string
  description = "RDS endpoint (hostname)"
}

variable "db_port" {
  type        = string
  description = "RDS port"
}

variable "db_name" {
  type        = string
  description = "Database name"
}

variable "db_username" {
  type        = string
  description = "Master username"
}

variable "ecr_repository_url" {
  type        = string
  description = "ECR repository URL for the migration container image"
}

variable "execution_role_arn" {
  type        = string
  description = "ECS task execution role ARN (for pull image, logs, secrets)"
}

variable "task_role_arn" {
  type        = string
  default     = null
  description = "ECS task role ARN (optional)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
