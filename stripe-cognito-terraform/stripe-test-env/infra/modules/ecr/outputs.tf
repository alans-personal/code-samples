output "repository_url" {
  description = "The URL of the repository"
  value       = aws_ecr_repository.main.repository_url
}

output "repository_arn" {
  description = "The ARN of the repository"
  value       = aws_ecr_repository.main.arn
}

output "repository_name" {
  description = "The name of the repository"
  value       = aws_ecr_repository.main.name
}

output "ecr_pull_policy" {
  description = "IAM policy document for ECS to pull images"
  value       = data.aws_iam_policy_document.ecr_pull.json
} 