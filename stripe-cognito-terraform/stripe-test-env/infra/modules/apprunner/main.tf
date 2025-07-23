locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "terraform"
      Service     = "apprunner"
    }
  )
}

# IAM Role for AppRunner to access ECR
resource "aws_iam_role" "apprunner_access_role" {
  name = "${local.name_prefix}-apprunner-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for AppRunner to pull images from ECR
resource "aws_iam_role_policy" "apprunner_ecr_policy" {
  name = "${local.name_prefix}-apprunner-ecr-policy"
  role = aws_iam_role.apprunner_access_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetAuthorizationToken",
          "logs:*"
        ]
        Resource = ["*"]
      }
    ]
  })
}

# CloudWatch Log Group for AppRunner
resource "aws_cloudwatch_log_group" "apprunner_logs" {
  name              = "/aws/apprunner/${local.name_prefix}-service"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# AppRunner Service
resource "aws_apprunner_service" "main" {
  service_name = var.service_name

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
    auto_deployments_enabled = var.auto_deploy_enabled
  }

  instance_configuration {
    cpu    = var.cpu
    memory = var.memory
    instance_role_arn = aws_iam_role.apprunner_access_role.arn
  }

  # Add health check configuration
  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"  # This will hit the NiceGUI health page
    interval = var.health_check_interval
    timeout  = var.health_check_timeout
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  # Add observability configuration - FIXED for AWS Provider 5.100.0
  dynamic "observability_configuration" {
    for_each = var.enable_observability ? [1] : []
    content {
      observability_enabled = true
      
      # Remove the trace_configuration block - it's not supported in this version
      # The tracing is handled automatically when observability_enabled = true
    }
  }

  tags = local.common_tags

  depends_on = [aws_iam_role_policy.apprunner_ecr_policy]
}

# CloudWatch Alarm for service health
resource "aws_cloudwatch_metric_alarm" "apprunner_health" {
  count = var.enable_monitoring ? 1 : 0
  
  alarm_name          = "${local.name_prefix}-apprunner-health"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/AppRunner"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "AppRunner service health check"
  
  dimensions = {
    ServiceName = aws_apprunner_service.main.service_name
  }

  tags = local.common_tags
} 