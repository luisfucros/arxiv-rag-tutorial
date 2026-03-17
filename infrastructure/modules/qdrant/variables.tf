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
  description = "Private subnet IDs for ECS service"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for ECS tasks"
}

variable "efs_file_system_id" {
  type        = string
  description = "EFS file system ID for Qdrant storage"
}

variable "efs_access_point_id" {
  type        = string
  description = "EFS access point ID for /qdrant/storage"
}

variable "execution_role_arn" {
  type        = string
  description = "ECS task execution role ARN"
}

variable "task_role_arn" {
  type        = string
  default     = null
  description = "ECS task role ARN (optional)"
}

variable "desired_count" {
  type        = number
  default     = 1
  description = "Desired number of Qdrant tasks"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
