data "aws_region" "current" {}

# ------------------------------------------------------------------------------
# IAM — task role for backend + worker (S3 artifacts)
# ------------------------------------------------------------------------------
resource "aws_iam_role" "app_task" {
  name_prefix = "${var.project_name}-app-task-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })

  tags = merge(var.tags, { Name = "${var.project_name}-app-task" })
}

resource "aws_iam_role_policy" "app_s3" {
  name = "artifacts-s3"
  role = aws_iam_role.app_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        var.artifacts_bucket_arn,
        "${var.artifacts_bucket_arn}/*"
      ]
    }]
  })
}

# ------------------------------------------------------------------------------
# Security groups — only the public ALB is open to the internet
# ------------------------------------------------------------------------------
resource "aws_security_group" "alb_public" {
  name_prefix = "${var.project_name}-alb-pub-"
  description = "Internet-facing ALB (frontend only)"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-alb-public" })
}

resource "aws_security_group" "alb_internal" {
  name_prefix = "${var.project_name}-alb-int-"
  description = "Internal ALB for API (VPC only)"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ECS tasks (nginx proxy)"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [var.ecs_tasks_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-alb-internal" })
}

# ------------------------------------------------------------------------------
# ECS cluster
# ------------------------------------------------------------------------------
resource "aws_ecs_cluster" "app" {
  name = "${var.project_name}-app"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = merge(var.tags, { Name = "${var.project_name}-app-cluster" })
}

locals {
  postgres_url = "postgresql://${var.db_username}:${var.db_password}@${var.db_endpoint}:${var.db_port}/${var.db_name}"
  redis_url_0  = "redis://${var.redis_host}:${var.redis_port}/0"
  redis_url_1  = "redis://${var.redis_host}:${var.redis_port}/1"
  frontend_url = coalesce(var.frontend_url_override, "http://${aws_lb.public.dns_name}")
}

# ------------------------------------------------------------------------------
# Public ALB → frontend
# ------------------------------------------------------------------------------
resource "aws_lb" "public" {
  name                       = "${var.project_name}-pub"
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb_public.id]
  subnets                    = var.public_subnet_ids
  drop_invalid_header_fields = true

  tags = merge(var.tags, { Name = "${var.project_name}-public-alb" })
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.project_name}-fe-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200-399"
  }

  tags = merge(var.tags, { Name = "${var.project_name}-frontend-tg" })
}

resource "aws_lb_listener" "public_http" {
  load_balancer_arn = aws_lb.public.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# ------------------------------------------------------------------------------
# Internal ALB → backend API (not reachable from the internet)
# ------------------------------------------------------------------------------
resource "aws_lb" "internal" {
  name                       = "${var.project_name}-api"
  internal                   = true
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb_internal.id]
  subnets                    = var.private_subnet_ids
  drop_invalid_header_fields = true

  tags = merge(var.tags, { Name = "${var.project_name}-internal-alb" })
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/openapi.json"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = merge(var.tags, { Name = "${var.project_name}-backend-tg" })
}

resource "aws_lb_listener" "internal_http" {
  load_balancer_arn = aws_lb.internal.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ------------------------------------------------------------------------------
# CloudWatch logs
# ------------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-backend"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}-frontend"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.project_name}-worker"
  retention_in_days = 7
  tags              = var.tags
}

# ------------------------------------------------------------------------------
# Task definitions
# ------------------------------------------------------------------------------
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.backend_cpu)
  memory                   = tostring(var.backend_memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = aws_iam_role.app_task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${var.ecr_urls["backend"]}:latest"
    essential = true
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    environment = [
      { name = "ENVIRONMENT", value = "production" },
      { name = "POSTGRES_DATABASE_URL", value = local.postgres_url },
      { name = "POSTGRES_ECHO_SQL", value = "false" },
      { name = "REDIS_HOST", value = var.redis_host },
      { name = "REDIS_PORT", value = tostring(var.redis_port) },
      { name = "REDIS_PASSWORD", value = "" },
      { name = "REDIS_DB", value = "2" },
      { name = "CELERY_BROKER_URL", value = local.redis_url_0 },
      { name = "CELERY_BACKEND_URL", value = local.redis_url_1 },
      { name = "VECTORDB_HOST", value = var.qdrant_nlb_dns },
      { name = "VECTORDB_PORT", value = "6333" },
      { name = "ARTIFACTS_BUKET", value = var.artifacts_bucket_name },
      { name = "FRONTEND_URL", value = local.frontend_url },
      { name = "AWS_DEFAULT_REGION", value = data.aws_region.current.name },
      { name = "OPENAI_API_KEY", value = var.openai_api_key },
      { name = "SECRET_KEY", value = var.jwt_secret },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = merge(var.tags, { Name = "${var.project_name}-backend" })
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.frontend_cpu)
  memory                   = tostring(var.frontend_memory)
  execution_role_arn       = var.execution_role_arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = "${var.ecr_urls["frontend"]}:latest"
    essential = true
    portMappings = [{
      containerPort = 80
      protocol      = "tcp"
    }]
    environment = [
      { name = "BACKEND_ORIGIN", value = "http://${aws_lb.internal.dns_name}" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = merge(var.tags, { Name = "${var.project_name}-frontend" })
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.worker_cpu)
  memory                   = tostring(var.worker_memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = aws_iam_role.app_task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = "${var.ecr_urls["data_ingestion"]}:latest"
    essential = true
    environment = [
      { name = "ENVIRONMENT", value = "production" },
      { name = "POSTGRES_DATABASE_URL", value = local.postgres_url },
      { name = "CELERY_BROKER_URL", value = local.redis_url_0 },
      { name = "CELERY_BACKEND_URL", value = local.redis_url_1 },
      { name = "VECTORDB_HOST", value = var.qdrant_nlb_dns },
      { name = "VECTORDB_PORT", value = "6333" },
      { name = "ARTIFACTS_BUKET", value = var.artifacts_bucket_name },
      { name = "AWS_DEFAULT_REGION", value = data.aws_region.current.name },
      { name = "OPENAI_API_KEY", value = var.openai_api_key },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = data.aws_region.current.name
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  tags = merge(var.tags, { Name = "${var.project_name}-worker" })
}

# ------------------------------------------------------------------------------
# ECS services
# ------------------------------------------------------------------------------
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent   = 100
  health_check_grace_period_seconds    = 60

  depends_on = [aws_lb_listener.internal_http]

  tags = merge(var.tags, { Name = "${var.project_name}-backend" })
}

resource "aws_ecs_service" "frontend" {
  name            = "${var.project_name}-frontend"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent   = 100
  health_check_grace_period_seconds    = 30

  depends_on = [aws_lb_listener.public_http]

  tags = merge(var.tags, { Name = "${var.project_name}-frontend" })
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project_name}-worker"
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_tasks_security_group_id]
    assign_public_ip = false
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 0

  tags = merge(var.tags, { Name = "${var.project_name}-worker" })
}
