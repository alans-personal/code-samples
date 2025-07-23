# Terraform Infrastructure Refactor: Replace ECS with AWS AppRunner

## Current Infrastructure Analysis
Based on the existing codebase, I can see you have:
- **VPC Module**: Creates VPC with public/private subnets, NAT Gateway, and routing
- **Cognito Module**: User authentication (to be preserved)
- **ECR Module**: Container registry with repository URL output: `${module.ecr.repository_url}`
- **ECS Module**: Complex ECS cluster with ALB, security groups, task definitions, and auto-scaling

## Task: Replace ECS with AppRunner for Simplified Deployment

### Objective
Remove the ECS cluster configuration and replace it with AWS AppRunner service while maintaining existing infrastructure components.

### Keep (Unchanged)
- ✅ **Cognito Module**: Preserve user authentication functionality
- ✅ **ECR Module**: Keep container registry (AppRunner will pull from ECR)
- ✅ **VPC Module**: Keep for potential future use or other services

### Remove/Replace
- ❌ **ECS Module**: Remove entire `infra/modules/ecs/` directory
- ❌ **ECS References**: Remove ECS module block from `infra/main.tf`
- ❌ **VPC Dependencies**: Remove VPC outputs from ECS module calls in main.tf

### Add (New Components)
- ➕ **AppRunner Module**: Create `infra/modules/apprunner/` with:
  - `main.tf` - AppRunner service configuration
  - `variables.tf` - Input variables
  - `outputs.tf` - Service URL and ARN outputs
- ➕ **AppRunner Module Block**: Add to `infra/main.tf`

### Required Changes

#### 1. Update `infra/main.tf`
```hcl
# Remove this entire block:
module "ecs" {
  source = "./modules/ecs"
  # ... all ECS configuration
}

# Add this new block:
module "apprunner" {
  source = "./modules/apprunner"
  
  environment = var.environment
  project     = var.project
  tags        = var.tags
  
  # ECR integration
  ecr_repository_url = module.ecr.repository_url
  ecr_repository_arn = module.ecr.repository_arn
  
  # AppRunner configuration
  service_name = "stripe-test-service"
  port         = 8000
  cpu          = "1024"
  memory       = "2048"
  
  # Environment variables
  environment_variables = {
    ENVIRONMENT = var.environment
  }
}
```

#### 2. Create `infra/modules/apprunner/main.tf`
```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "terraform"
    }
  )
}

# AppRunner Service
resource "aws_apprunner_service" "main" {
  service_name = var.service_name

  source_configuration {
    image_repository {
      image_configuration {
        port = var.port
        runtime_environment_variables = var.environment_variables
      }
      image_identifier      = "${var.ecr_repository_url}:latest"
      image_repository_type = "ECR"
    }
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu    = var.cpu
    memory = var.memory
  }

  tags = local.common_tags
}
```

#### 3. Create `infra/modules/apprunner/variables.tf`
```hcl
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
  default     = 10
  
  validation {
    condition     = var.health_check_interval >= 1 && var.health_check_interval <= 30
    error_message = "Health check interval must be between 1 and 30 seconds."
  }
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
  
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
```

#### 4. Create `infra/modules/apprunner/outputs.tf`
```hcl
output "service_url" {
  description = "AppRunner service URL"
  value       = aws_apprunner_service.main.service_url
}

output "service_arn" {
  description = "AppRunner service ARN"
  value       = aws_apprunner_service.main.arn
}

output "service_id" {
  description = "AppRunner service ID"
  value       = aws_apprunner_service.main.id
}

output "service_status" {
  description = "AppRunner service status"
  value       = aws_apprunner_service.main.status
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.apprunner_logs.name
}

output "iam_role_arn" {
  description = "IAM role ARN for AppRunner"
  value       = aws_iam_role.apprunner_access_role.arn
}
```

### Key Benefits of AppRunner
- **Simplified Deployment**: No need for ALB, security groups, or complex networking
- **Auto-scaling**: Built-in scaling based on CPU/memory usage
- **Managed Infrastructure**: AWS handles the underlying compute resources
- **Direct ECR Integration**: Seamless container image deployment
- **Built-in HTTPS**: Automatic SSL certificate management

### Migration Steps
1. Create the new AppRunner module files
2. Update `infra/main.tf` to replace ECS with AppRunner
3. Run `terraform plan` to verify changes
4. Run `terraform apply` to deploy AppRunner
5. Test the new service URL
6. Remove the old ECS module directory

### Important Notes
- AppRunner uses AWS-managed networking (no VPC required)
- The service will be accessible via the AppRunner service URL
- Auto-deploy is enabled for seamless updates when new images are pushed to ECR
- Environment variables are preserved from the ECS configuration
- All existing tagging conventions are maintained

### Documentation References
- [AWS AppRunner Documentation](https://docs.aws.amazon.com/apprunner/)
- [Terraform AWS AppRunner Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apprunner_service)
- [AppRunner with ECR](https://docs.aws.amazon.com/apprunner/latest/dg/manage-create.html)