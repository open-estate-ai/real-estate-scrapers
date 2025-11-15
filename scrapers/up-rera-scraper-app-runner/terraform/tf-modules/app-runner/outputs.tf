output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.scraper.repository_url
}

output "app_runner_service_url" {
  description = "URL of the App Runner service"
  value       = try("https://${aws_apprunner_service.scraper_service.service_url}", "Not created yet - run 'terraform apply' after deploying Docker image")
}

output "app_runner_service_id" {
  description = "ID of the App Runner service"
  value       = try(aws_apprunner_service.scraper_service.id, "Not created yet")
}

output "app_runner_instance_role_arn" {
  description = "ARN of the App Runner instance role"
  value       = aws_iam_role.app_runner_instance_role.arn
}

output "app_runner_service_name" {
  description = "Name of App Runner Service Name"
  value       = local.app_runner_service_name
}
