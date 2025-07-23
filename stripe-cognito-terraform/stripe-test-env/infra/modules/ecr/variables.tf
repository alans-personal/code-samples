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

variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "stripe-test"
}

variable "image_retention_count" {
  description = "Number of untagged images to retain"
  type        = number
  default     = 30
} 