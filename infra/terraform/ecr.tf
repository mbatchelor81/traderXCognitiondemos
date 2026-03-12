resource "aws_ecr_repository" "services" {
  for_each = toset([
    "account-service",
    "trading-service",
    "position-service",
    "reference-data-service",
    "people-service",
    "web-frontend",
  ])

  name         = "traderx-${each.key}-${var.tenant_id}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(local.common_tags, {
    Service = each.key
  })
}
