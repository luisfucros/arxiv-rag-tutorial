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

output "private_subnet_ids" {
  value       = module.vpc.private_subnet_ids
  description = "Private subnet IDs (Fargate tasks, migration run-task)"
}

output "ecs_app_service_names" {
  value = {
    backend  = module.ecs_app.ecs_service_name_backend
    frontend = module.ecs_app.ecs_service_name_frontend
    worker   = module.ecs_app.ecs_service_name_worker
  }
  description = "ECS service names on the app cluster (for force-new-deployment)"
}

output "public_alb_dns_name" {
  value       = module.ecs_app.public_alb_dns_name
  description = "Public ALB DNS — open http://<this> for the SPA (only internet-facing entry point)"
}

output "ecs_app_cluster_name" {
  value       = module.ecs_app.ecs_cluster_name
  description = "ECS cluster hosting frontend, backend, and ingestion worker"
}

output "ecr_repository_urls" {
  value       = module.ecr.repository_urls
  description = "Push images: migration (db migrate task), backend, frontend, data_ingestion"
}

output "qdrant_nlb_dns" {
  value       = module.qdrant.nlb_dns_name
  description = "Internal Qdrant NLB DNS (VPC only)"
}
