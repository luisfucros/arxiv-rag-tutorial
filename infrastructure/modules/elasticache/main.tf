resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.project_name}-redis-subnet"
  })
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id      = "${var.project_name}-${var.elasticache_cluster_id}"
  engine          = var.elasticache_engine
  node_type       = var.elasticache_node_type
  num_cache_nodes = 1
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.security_group_id]

  tags = merge(var.tags, {
    Name = "${var.project_name}-redis"
  })
}