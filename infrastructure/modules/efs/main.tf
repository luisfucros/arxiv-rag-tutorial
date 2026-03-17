resource "aws_efs_file_system" "main" {
  creation_token = "${var.project_name}-qdrant-storage"
  encrypted      = true

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-efs"
  })
}

resource "aws_efs_mount_target" "main" {
  count           = length(var.private_subnet_ids)
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = var.private_subnet_ids[count.index]
  security_groups = [var.security_group_id]
}

resource "aws_efs_access_point" "qdrant" {
  file_system_id = aws_efs_file_system.main.id

  posix_user {
    gid = 1000
    uid = 1000
  }

  root_directory {
    path = "/qdrant"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "0755"
    }
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-qdrant-ap"
  })
}
