locals {
  services = [
    "account-service",
    "trading-service",
    "position-service",
    "reference-data-service",
    "people-service",
  ]
}

resource "aws_ecr_repository" "services" {
  for_each     = toset(local.services)
  name         = "traderx-${each.key}-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Service     = each.key
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}
