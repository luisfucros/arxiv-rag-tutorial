resource "aws_ecs_cluster" "qdrant" {
  name = "${var.project_name}-qdrant-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-cluster"
  })
}

resource "aws_ecs_task_definition" "qdrant" {
  family                   = "${var.project_name}-qdrant"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  volume {
    name = "qdrant-storage"

    efs_volume_configuration {
      file_system_id     = var.efs_file_system_id
      transit_encryption = "ENABLED"
      
      root_directory = "/"
      
      authorization_config {
        access_point_id = var.efs_access_point_id
      }
    }
  }

  container_definitions = jsonencode([
    {
      name  = "qdrant"
      image = "qdrant/qdrant:v1.16"

      essential = true

      portMappings = [
        { containerPort = 6333, protocol = "tcp", name = "http" },
        { containerPort = 6334, protocol = "tcp", name = "grpc" }
      ]

      mountPoints = [
        {
          sourceVolume  = "qdrant-storage"
          containerPath = "/qdrant/storage"
          readOnly      = false
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"          = "/ecs/${var.project_name}-qdrant"
          "awslogs-region"         = data.aws_region.current.name
          "awslogs-stream-prefix"  = "ecs"
        }
      }

    #   healthCheck = null
    }
  ])

  depends_on = [aws_cloudwatch_log_group.ecs_qdrant]

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant"
  })
}

# Logs
resource "aws_cloudwatch_log_group" "ecs_qdrant" {
  name              = "/ecs/${var.project_name}-qdrant"
  retention_in_days = 7
}

 # NLB so EKS can reach Qdrant at a stable hostname
resource "aws_lb" "qdrant" {
  name               = "${var.project_name}-qdrant-nlb"
  internal           = true
  load_balancer_type = "network"
  subnets            = var.private_subnet_ids
  security_groups    = []

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-nlb"
  })
}

resource "aws_lb_target_group" "qdrant_grpc" {
  name        = "${var.project_name}-qdrant-grpc"
  port        = 6333
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    protocol            = "HTTP"
    port                = "6334"
    path                = "/readyz"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-grpc-tg"
  })
}

resource "aws_lb_target_group" "qdrant_http" {
  name        = "${var.project_name}-qdrant-http"
  port        = 6334
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    protocol            = "HTTP"
    port                = "6334"
    path                = "/readyz"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-http-tg"
  })
}

resource "aws_lb_listener" "qdrant_grpc" {
  load_balancer_arn = aws_lb.qdrant.arn
  port              = 6333
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.qdrant_grpc.arn
  }
}

resource "aws_lb_listener" "qdrant_http" {
  load_balancer_arn = aws_lb.qdrant.arn
  port              = 6334
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.qdrant_http.arn
  }
}

resource "aws_ecs_service" "qdrant" {
  name            = "${var.project_name}-qdrant"
  cluster         = aws_ecs_cluster.qdrant.id
  task_definition = aws_ecs_task_definition.qdrant.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = false
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 0

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant"
  })
}

data "aws_region" "current" {}