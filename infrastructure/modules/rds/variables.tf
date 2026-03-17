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
  description = "Private subnet IDs for RDS"
}

# variable "public_subnet_ids" {
#   type        = list(string)
#   description = "Public subnet IDs for RDS"
# }

variable "security_group_id" {
  type        = string
  description = "Security group ID for RDS"
}

variable "db_name" {
  type        = string
  default     = "rag_db"
  description = "Database name"
}

variable "db_username" {
  type        = string
  default     = "rag_user"
  description = "Master username (stored in Secrets Manager when manage_master_user_password is true)"
}

variable "engine_version" {
  type        = string
  default     = "16"
  description = "PostgreSQL major version"
}

variable "instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "RDS instance class"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Allocated storage in GB"
}

variable "manage_master_user_password" {
  type        = bool
  default     = false
  description = "Let RDS manage master password in Secrets Manager"
}

variable "db_password" {
  type        = string
  default     = "rag_password"
  sensitive   = true
  description = "Master password (if set, manage_master_user_password should be false)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
