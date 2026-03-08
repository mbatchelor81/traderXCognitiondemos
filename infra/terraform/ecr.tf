resource "aws_ecr_repository" "users_service" {
  name         = "${local.app_name}-users-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name     = "${local.app_name}-users-service-${var.tenant_id}"
    Service  = "users-service"
    TenantID = var.tenant_id
  }
}

resource "aws_ecr_repository" "trades_service" {
  name         = "${local.app_name}-trades-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name     = "${local.app_name}-trades-service-${var.tenant_id}"
    Service  = "trades-service"
    TenantID = var.tenant_id
  }
}

resource "aws_ecr_repository" "web_frontend" {
  name         = "${local.app_name}-web-frontend-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name     = "${local.app_name}-web-frontend-${var.tenant_id}"
    Service  = "web-frontend"
    TenantID = var.tenant_id
  }
}
