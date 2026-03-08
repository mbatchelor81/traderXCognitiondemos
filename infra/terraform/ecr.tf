resource "aws_ecr_repository" "users_service" {
  name         = "traderx-users-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "traderx-users-service-${var.tenant_id}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}

resource "aws_ecr_repository" "trades_service" {
  name         = "traderx-trades-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "traderx-trades-service-${var.tenant_id}"
    Environment = var.environment
    TenantID    = var.tenant_id
  }
}
