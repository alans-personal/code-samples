# ECR Infrastructure Audit and Fix

## Current State
- ECR Repository: stripe-test
- Region: us-west-2
- Current Issues:
  1. ECR repository configuration needs verification
  2. AppRunner service needs proper ECR image configuration
  3. Missing proper health check configuration for AppRunner
  4. IAM roles need proper ECR pull permissions for AppRunner

## Required Changes

### 1. ECR Repository Configuration
- Verify ECR repository settings:
  ```hcl
  resource "aws_ecr_repository" "main" {
    name                 = var.repository_name
    image_tag_mutability = "MUTABLE"
    
    image_scanning_configuration {
      scan_on_push = true
    }
  }
  ```

### 2. ECR Lifecycle Policy
- Configure image cleanup:
  ```hcl
  resource "aws_ecr_lifecycle_policy" "main" {
    repository = aws_ecr_repository.main.name
    
    policy = jsonencode({
      rules = [
        {
          rulePriority = 1
          description  = "Keep last 5 images"
          selection = {
            tagStatus     = "untagged"
            countType     = "imageCountMoreThan"
            countNumber   = 5
          }
          action = {
            type = "expire"
          }
        }
      ]
    })
  }
  ```

### 3. AppRunner Service Configuration
- Update AppRunner to use ECR:
  ```hcl
  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }
    
    image_repository {
      image_configuration {
        port = var.port
        runtime_environment_variables = var.environment_variables
      }
      image_identifier      = "${var.ecr_repository_url}:latest"
      image_repository_type = "ECR"
    }
  }
  ```

### 4. IAM Roles and Permissions for AppRunner
- Verify AppRunner access role has:
  ```hcl
  resource "aws_iam_role_policy" "apprunner_ecr_policy" {
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Effect = "Allow"
          Action = [
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetAuthorizationToken"
          ]
          Resource = ["*"]
        }
      ]
    })
  }
  ```

### 5. AppRunner Health Check Configuration
- Configure health checks for AppRunner:
  ```hcl
  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
    interval = 5
    timeout  = 2
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }
  ```

## Implementation Steps
1. Verify ECR repository configuration
2. Update AppRunner service configuration
3. Configure proper IAM roles for AppRunner
4. Set up health check endpoints
5. Test deployment

## Validation Checklist
- [ ] ECR repository is accessible
- [ ] AppRunner service can pull images from ECR
- [ ] IAM roles have proper ECR permissions
- [ ] Health checks are passing
- [ ] Application is accessible through AppRunner URL
- [ ] Docker images can be pushed to ECR successfully

## Docker Image Management
- Use `build-and-push.sh` script to build and push images
- Ensure images are tagged with `latest` for AppRunner deployment
- Verify image architecture compatibility (x86_64 for AppRunner)

Note:
Please use the latest **Sonnet v4 (GPT-4o)** model for improved accuracy in Terraform structure and AWS resource design.