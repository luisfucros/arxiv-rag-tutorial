terraform {
  required_version = "~> 1.6"
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    null = {
      source = "hashicorp/null"
      version = "~> 3.2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
    })
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  project_name     = var.project_name
  azs              = slice(data.aws_availability_zones.available.names, 0, 3)
  public_cidrs    = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i)]
  private_cidrs   = [for i in range(3) : cidrsubnet(var.vpc_cidr, 8, i + 10)]
}

# ------------------------------------------------------------------------------
# VPC
# ------------------------------------------------------------------------------
module "vpc" {
  source = "./modules/vpc"

  project_name           = local.project_name
  vpc_cidr               = var.vpc_cidr
  azs                    = local.azs
  public_subnet_cidrs    = local.public_cidrs
  private_subnet_cidrs   = local.private_cidrs
  enable_nat_gateway     = true
  tags                   = var.tags
}

# ------------------------------------------------------------------------------
# S3 artifacts bucket
# ------------------------------------------------------------------------------
module "s3" {
  source = "./modules/s3"

  project_name           = local.project_name
  artifacts_bucket_name  = var.artifacts_bucket_name
  tags                   = var.tags
}

# ------------------------------------------------------------------------------
# RDS
# ------------------------------------------------------------------------------
module "rds" {
  source = "./modules/rds"

  project_name                  = local.project_name
  vpc_id                        = module.vpc.vpc_id
  private_subnet_ids            = module.vpc.private_subnet_ids
  # public_subnet_ids             = module.vpc.public_subnet_ids
  security_group_id             = module.vpc.security_group_rds_id
  db_name                       = "rag_db"
  db_username                   = "rag_user"
  db_password                   = var.db_password
  engine_version                = "16"
  instance_class                = "db.t3.micro"
  allocated_storage             = 20
  manage_master_user_password   = false
  tags                          = var.tags
}

# ------------------------------------------------------------------------------
# ElastiCache Redis
# ------------------------------------------------------------------------------
# module "elasticache" {
#   source = "./modules/elasticache"

#   project_name            = local.project_name
#   vpc_id                  = module.vpc.vpc_id
#   private_subnet_ids      = module.vpc.private_subnet_ids
#   security_group_id       = module.vpc.security_group_redis_id
#   elasticache_node_type   = "cache.t3.micro"
#   tags                    = var.tags
# }

# ------------------------------------------------------------------------------
# ECR
# ------------------------------------------------------------------------------
module "ecr" {
  source = "./modules/ecr"

  project_name    = local.project_name
  repository_name = var.repository_name
  environment     = var.environment
  tags            = var.tags
}

# ------------------------------------------------------------------------------
# EFS for Qdrant
# ------------------------------------------------------------------------------
module "efs" {
  source = "./modules/efs"

  project_name        = local.project_name
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  security_group_id   = module.vpc.security_group_efs_id
  tags                = var.tags
}

# ------------------------------------------------------------------------------
# ECS execution/task roles (for migration and Qdrant)
# ------------------------------------------------------------------------------
resource "aws_iam_role" "ecs_execution" {
  name_prefix = "${local.project_name}-ecs-exec-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })

  tags = merge(var.tags, { Name = "${local.project_name}-ecs-execution" })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ------------------------------------------------------------------------------
# ECS Migration
# ------------------------------------------------------------------------------
module "migration" {
  source = "./modules/migration"

  project_name        = local.project_name
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  security_group_id   = module.vpc.security_group_ecs_tasks_id
  db_password         = var.db_password
  db_endpoint         = module.rds.endpoint
  db_port             = module.rds.port
  db_name             = module.rds.db_name
  db_username         = module.rds.db_username
  ecr_repository_url  = module.ecr.repository_url
  execution_role_arn  = aws_iam_role.ecs_execution.arn
  tags                = var.tags
}

# ------------------------------------------------------------------------------
# ECS Qdrant
# ------------------------------------------------------------------------------
module "qdrant" {
  source = "./modules/qdrant"

  project_name          = local.project_name
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  security_group_id     = module.vpc.security_group_ecs_tasks_id
  efs_file_system_id    = module.efs.file_system_id
  efs_access_point_id   = module.efs.access_point_id
  execution_role_arn    = aws_iam_role.ecs_execution.arn
  desired_count         = 1
  tags                  = var.tags
}