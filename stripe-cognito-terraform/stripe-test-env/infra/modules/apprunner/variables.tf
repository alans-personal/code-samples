variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project" {
  description = "Project name"
  type        = string
  
  validation {
    condition     = length(var.project) >= 3 && length(var.project) <= 50
    error_message = "Project name must be between 3 and 50 characters."
  }
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
}

variable "service_name" {
  description = "Name of the AppRunner service"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}

variable "ecr_repository_arn" {
  description = "ECR repository ARN"
  type        = string
}

variable "port" {
  description = "Container port"
  type        = number
  default     = 8000
  
  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Port must be between 1 and 65535."
  }
}

variable "cpu" {
  description = "CPU units (1024 = 1 vCPU)"
  type        = string
  default     = "1024"
  
  validation {
    condition     = contains(["256", "512", "1024", "2048", "4096"], var.cpu)
    error_message = "CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Memory in MB"
  type        = string
  default     = "2048"
  
  validation {
    condition     = contains(["512", "1024", "2048", "3072", "4096", "6144", "8192"], var.memory)
    error_message = "Memory must be one of: 512, 1024, 2048, 3072, 4096, 6144, 8192."
  }
}

variable "environment_variables" {
  description = "Environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "auto_deploy_enabled" {
  description = "Enable automatic deployments"
  type        = bool
  default     = true
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 20
  
  validation {
    condition     = var.health_check_interval >= 1 && var.health_check_interval <= 20
    error_message = "Health check interval must be between 1 and 20 seconds."
  }
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 3
  
  validation {
    condition     = var.health_check_timeout >= 1 && var.health_check_timeout <= 10
    error_message = "Health check timeout must be between 1 and 10 seconds."
  }
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks"
  type        = number
  default     = 1
  
  validation {
    condition     = var.health_check_healthy_threshold >= 1 && var.health_check_healthy_threshold <= 10
    error_message = "Healthy threshold must be between 1 and 10."
  }
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks"
  type        = number
  default     = 2
  
  validation {
    condition     = var.health_check_unhealthy_threshold >= 1 && var.health_check_unhealthy_threshold <= 10
    error_message = "Unhealthy threshold must be between 1 and 10."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be one of the allowed values."
  }
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "enable_observability" {
  description = "Enable observability configuration with AWS X-Ray tracing"
  type        = bool
  default     = false
} 