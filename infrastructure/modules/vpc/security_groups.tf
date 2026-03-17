# RDS: 5432 from EKS and ECS only
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds"
  description = "RDS PostgreSQL; allow 5432 from EKS and ECS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "PostgreSQL from EKS and ECS"
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

# Redis: 6379 from EKS and ECS
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  description = "ElastiCache Redis; allow 6379 from EKS and ECS"
  vpc_id      = aws_vpc.main.id

ingress {
    description = "Allow all inbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "Redis from EKS and ECS"
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

# ECS tasks (Qdrant + migration): 6333 from EKS; allow EFS
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-ecs-tasks-"
  description = "ECS tasks (Qdrant, migration); allow 6333 from EKS; EFS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow all inbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ingress {
  #   from_port       = 6333
  #   to_port         = 6333
  #   protocol        = "tcp"
  #   security_groups = [aws_security_group.eks_nodes.id]
  #   description     = "Qdrant gRPC from EKS"
  # }

  # ingress {
  #   from_port       = 6334
  #   to_port         = 6334
  #   protocol        = "tcp"
  #   security_groups = [aws_security_group.eks_nodes.id]
  #   description     = "Qdrant REST from EKS"
  # }

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