output "public_alb_dns_name" {
  value       = aws_lb.public.dns_name
  description = "Public ALB DNS — use this URL for the SPA; set frontend_public_url / CORS to match"
}

output "internal_alb_dns_name" {
  value       = aws_lb.internal.dns_name
  description = "Private API load balancer DNS (VPC only)"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.app.name
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.app.arn
}

output "ecs_service_name_backend" {
  value = aws_ecs_service.backend.name
}

output "ecs_service_name_frontend" {
  value = aws_ecs_service.frontend.name
}

output "ecs_service_name_worker" {
  value = aws_ecs_service.worker.name
}
