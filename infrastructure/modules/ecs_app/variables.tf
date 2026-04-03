variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "ecs_tasks_security_group_id" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "ecr_urls" {
  type        = map(string)
  description = "Map with keys backend, frontend, data_ingestion"
}

variable "db_endpoint" {
  type = string
}

variable "db_port" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "redis_host" {
  type = string
}

variable "redis_port" {
  type    = number
  default = 6379
}

variable "qdrant_nlb_dns" {
  type        = string
  description = "Internal NLB DNS name for Qdrant (HTTP on 6333)"
}

variable "artifacts_bucket_name" {
  type = string
}

variable "artifacts_bucket_arn" {
  type = string
}

variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "frontend_url_override" {
  type        = string
  default     = null
  nullable    = true
  description = "If set, used for CORS (FRONTEND_URL). Otherwise http://<public ALB DNS> from this module."
}

variable "backend_desired_count" {
  type    = number
  default = 1
}

variable "frontend_desired_count" {
  type    = number
  default = 1
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "worker_cpu" {
  type    = number
  default = 1024
}

variable "worker_memory" {
  type    = number
  default = 2048
}

variable "tags" {
  type    = map(string)
  default = {}
}
