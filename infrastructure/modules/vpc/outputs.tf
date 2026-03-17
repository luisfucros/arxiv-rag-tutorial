output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "vpc_cidr" {
  value       = aws_vpc.main.cidr_block
  description = "VPC CIDR"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs"
}

# output "security_group_alb_id" {
#   value       = aws_security_group.alb.id
#   description = "ALB security group ID"
# }

# output "security_group_eks_nodes_id" {
#   value       = aws_security_group.eks_nodes.id
#   description = "EKS nodes security group ID"
# }

output "security_group_rds_id" {
  value       = aws_security_group.rds.id
  description = "RDS security group ID"
}

output "security_group_redis_id" {
  value       = aws_security_group.redis.id
  description = "Redis security group ID"
}

output "security_group_ecs_tasks_id" {
  value       = aws_security_group.ecs_tasks.id
  description = "ECS tasks security group ID"
}

output "security_group_efs_id" {
  value       = aws_security_group.efs.id
  description = "EFS security group ID"
}
