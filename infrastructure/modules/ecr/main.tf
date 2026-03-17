resource "aws_ecr_repository" "migration" {
  name = "${var.project_name}-${var.repository_name}-${var.environment}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecr"
  })
}