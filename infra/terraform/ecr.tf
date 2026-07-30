# One ECR repository per workload:
#   traderx-account-service-acme-corp
#   traderx-trading-service-acme-corp
#   traderx-position-service-acme-corp
#   traderx-reference-data-service-acme-corp
#   traderx-people-service-acme-corp
#   traderx-web-frontend-acme-corp

resource "aws_ecr_repository" "this" {
  for_each = local.workloads

  name                 = local.ecr_repository_names[each.value]
  image_tag_mutability = "MUTABLE"

  # Demo convenience: allows `terraform destroy` to remove repositories that still
  # contain images. Do not enable this in production.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(local.common_tags, {
    Name     = local.ecr_repository_names[each.value]
    Workload = each.value
  })
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
