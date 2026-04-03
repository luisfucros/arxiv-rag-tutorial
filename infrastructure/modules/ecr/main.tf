resource "aws_ecr_repository" "this" {
  for_each = var.repositories

  name = "${var.project_name}-${each.value}-${var.environment}"

  tags = merge(var.tags, {
    Name = "${var.project_name}-ecr-${each.key}"
  })
}
