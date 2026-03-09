resource "aws_ecr_repository" "users_service" {
  name         = "traderx-users-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "traderx-users-service-${var.tenant_id}"
    Service = "users-service"
  }
}

resource "aws_ecr_repository" "trades_service" {
  name         = "traderx-trades-service-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "traderx-trades-service-${var.tenant_id}"
    Service = "trades-service"
  }
}

resource "aws_ecr_repository" "frontend" {
  name         = "traderx-frontend-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "traderx-frontend-${var.tenant_id}"
    Service = "frontend"
  }
}
