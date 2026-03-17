output "cluster_name" {
  value       = aws_ecs_cluster.migration.name
  description = "ECS cluster name for migration"
}

output "cluster_arn" {
  value       = aws_ecs_cluster.migration.arn
  description = "ECS cluster ARN"
}

output "task_definition_arn" {
  value       = aws_ecs_task_definition.migration.arn
  description = "Task definition ARN (run manually or via CI: aws ecs run-task)"
}

output "task_family" {
  value       = aws_ecs_task_definition.migration.family
  description = "Task definition family"
}
