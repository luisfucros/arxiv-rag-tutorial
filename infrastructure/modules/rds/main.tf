resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-rds-subnet"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.project_name}-rds-subnet"
  })
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-postgres"
  engine         = "postgres"
  engine_version = var.engine_version

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  instance_class        = var.instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.allocated_storage * 2

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  publicly_accessible    = false
  multi_az               = false

  skip_final_snapshot       = true
  deletion_protection       = false
  backup_retention_period   = 7
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:00-sun:05:00"

  tags = merge(var.tags, {
    Name = "${var.project_name}-postgres"
  })
}