output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.app_runner.ecr_repository_url
}

output "app_runner_service_url" {
  description = "URL of the App Runner service"
  value       = module.app_runner.app_runner_service_url
}

output "app_runner_service_id" {
  description = "ID of the App Runner service"
  value       = try(module.app_runner.app_runner_service_id, "Not created yet")
}

output "app_runner_instance_role_arn" {
  description = "ARN of the App Runner instance role"
  value       = module.app_runner.app_runner_instance_role_arn
}

output "app_runner_service_name" {
  description = "Name of App Runner Service Name"
  value       = module.app_runner.app_runner_service_name
}
