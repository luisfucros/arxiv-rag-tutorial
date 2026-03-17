# Migration outputs
output "migration_cluster_arn" {
  value       = module.migration.cluster_arn
  description = "ECS cluster ARN for migration tasks"
}

output "migration_cluster_name" {
  value       = module.migration.cluster_name
  description = "ECS cluster name for migration tasks"
}

output "migration_task_definition_arn" {
  value       = module.migration.task_definition_arn
  description = "Migration task definition ARN"
}

# VPC outputs for migration task networking
output "ecs_security_group_id" {
  value       = module.vpc.security_group_ecs_tasks_id
  description = "Security group ID for ECS tasks"
}

output "public_subnet_ids" {
  value       = module.vpc.public_subnet_ids
  description = "Public subnet IDs"
}
