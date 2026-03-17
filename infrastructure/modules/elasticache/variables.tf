variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "elasticache_cluster_id" {
  description = "ID of the elasticache cluster"
  type        = string
  default   = "redis-cluster"
}

variable "elasticache_engine" {
  description = "Elasticache Engine"
  type        = string
  default   = "redis"
}

variable "elasticache_node_type" {
  description = "Elasticache Node Type"
  type        = string
  default   = "cache.t3.micro"
}

variable "elasticache_subnet_group_name" {
  description = "Elasticache Subset Group Name"
  type        = string
  default   = "redis-subnet-group"
}

variable "elasticache_port" {
  description = "Elasticache Port"
  type        = number
  default     = 6379
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

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
