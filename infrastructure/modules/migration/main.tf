resource "aws_ecs_cluster" "migration" {
  name = "${var.project_name}-migration-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-migration-cluster"
  })
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "${var.project_name}-migration"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name  = "migrations"
      image = "${var.ecr_repository_url}:latest"

      essential = true

      environment = [
        {
          name      = "POSTGRES_DATABASE_URL"
          value     = "postgresql://${var.db_username}:${var.db_password}@${var.db_endpoint}:${var.db_port}/${var.db_name}"
        }
      ]

      secrets = [
        
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-migration"
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  depends_on = [aws_cloudwatch_log_group.ecs_migration]

  tags = merge(var.tags, {
    Name = "${var.project_name}-migration"
  })
}

# Logs
resource "aws_cloudwatch_log_group" "ecs_migration" {
  name              = "/ecs/${var.project_name}-migration"
  retention_in_days = 7
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
