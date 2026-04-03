# RDS: 5432 from ECS tasks only
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds"
  description = "RDS PostgreSQL; allow 5432 from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "PostgreSQL from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-rds-sg"
  })
}

# Redis: 6379 from ECS tasks only
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  description = "ElastiCache Redis; allow 6379 from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "Redis from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-redis-sg"
  })
}

# ECS tasks (app, Qdrant, migration): VPC-only ingress (tightened via rules below + attachments)
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-ecs-tasks-"
  description = "ECS Fargate tasks; ingress from VPC, public ALB, and internal ALB (see separate rules)"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Task-to-task traffic inside VPC (backend, worker, Qdrant, NLB health checks)"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecs-tasks-sg"
  })
}

# EFS: NFS from ECS tasks (Qdrant)
resource "aws_security_group" "efs" {
  name_prefix = "${var.project_name}-efs-"
  description = "EFS for Qdrant storage; NFS from ECS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "NFS from ECS Qdrant"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-efs-sg"
  })
}