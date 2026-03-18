output "file_system_id" {
  value       = aws_efs_file_system.main.id
  description = "EFS file system ID"
}

output "file_system_arn" {
  value       = aws_efs_file_system.main.arn
  description = "EFS file system ARN"
}

output "access_point_id" {
  value       = aws_efs_access_point.qdrant.id
  description = "EFS access point ID for Qdrant volume"
}

output "access_point_arn" {
  value       = aws_efs_access_point.qdrant.arn
  description = "EFS access point ARN"
}

output "mount_target_ids" {
  value       = aws_efs_mount_target.main[*].id
  description = "EFS mount target IDs (one per private subnet); tasks must run in these subnets to resolve EFS DNS"
}
