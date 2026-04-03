output "redis_address" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "Primary Redis node hostname"
}

output "redis_port" {
  value       = aws_elasticache_cluster.redis.port
  description = "Redis port (typically 6379)"
}

output "redis_connection_string" {
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}"
  description = "host:port for Redis clients"
}
