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