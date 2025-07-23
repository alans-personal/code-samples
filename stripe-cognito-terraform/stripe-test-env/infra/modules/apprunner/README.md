# AppRunner Module

This module deploys an AWS AppRunner service with ECR integration, monitoring, and health checks.

## Usage

```hcl
module "apprunner" {
  source = "./modules/apprunner"
  
  environment = "dev"
  project     = "my-project"
  tags        = var.tags
  
  service_name = "my-service"
  ecr_repository_url = module.ecr.repository_url
  ecr_repository_arn = module.ecr.repository_arn
  
  port         = 8000
  cpu          = "1024"
  memory       = "2048"
  
  environment_variables = {
    ENVIRONMENT = "dev"
    API_KEY     = var.api_key
  }
  
  health_check_path = "/health"
  enable_monitoring = true
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| environment | Environment name | `string` | n/a | yes |
| project | Project name | `string` | n/a | yes |
| service_name | Name of the AppRunner service | `string` | n/a | yes |
| ecr_repository_url | ECR repository URL | `string` | n/a | yes |
| ecr_repository_arn | ECR repository ARN | `string` | n/a | yes |
| port | Container port | `number` | `8000` | no |
| cpu | CPU units | `string` | `"1024"` | no |
| memory | Memory in MB | `string` | `"2048"` | no |
| environment_variables | Environment variables | `map(string)` | `{}` | no |
| health_check_path | Health check path | `string` | `"/health"` | no |
| enable_monitoring | Enable CloudWatch monitoring | `bool` | `true` | no |

## Outputs

| Name | Description |
|------|-------------|
| service_url | AppRunner service URL |
| service_arn | AppRunner service ARN |
| service_id | AppRunner service ID |
| service_status | AppRunner service status |
| log_group_name | CloudWatch log group name |
| iam_role_arn | IAM role ARN for AppRunner |

## Security

- IAM role with minimal required permissions for ECR access
- CloudWatch logging enabled
- Health checks configured
- Monitoring alarms for service health 