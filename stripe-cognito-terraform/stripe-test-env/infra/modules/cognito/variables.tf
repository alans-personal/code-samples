variable "environment" {
  description = "Environment name (e.g., dev, test, prod)"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
} 