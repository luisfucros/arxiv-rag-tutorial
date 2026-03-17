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
  description = "Private subnet IDs for EFS mount targets"
}

variable "security_group_id" {
  type        = string
  description = "Security group ID for EFS"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
