variable "project_name" {
  type        = string
  default     = "arxiv-rag"
  description = "Project name"
}

variable "artifacts_bucket_name" {
  type        = string
  description = "Name of the S3 bucket for PDF artifacts (must be globally unique)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags"
}
