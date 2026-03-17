output "endpoint" {
  value       = aws_db_instance.main.address
  description = "RDS endpoint (hostname)"
}

output "port" {
  value       = aws_db_instance.main.port
  description = "RDS port"
}

output "db_name" {
  value       = aws_db_instance.main.db_name
  description = "Database name"
}

output "db_username" {
  value       = aws_db_instance.main.username
  description = "Master username"
}
