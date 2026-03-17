variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR for the VPC"
}

variable "azs" {
  type        = list(string)
  description = "Availability zones for subnets"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for public subnets (one per AZ)"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for private subnets (one per AZ)"
}

variable "enable_nat_gateway" {
  type        = bool
  default     = true
  description = "Create NAT gateway for private subnet egress"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all resources"
}
