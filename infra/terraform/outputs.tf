output "alb_url" {
  description = "ALB DNS name for accessing services"
  value       = aws_lb.traderx.dns_name
}

output "ecr_users_service_url" {
  description = "ECR repository URL for users-service"
  value       = aws_ecr_repository.users_service.repository_url
}

output "ecr_trades_service_url" {
  description = "ECR repository URL for trades-service"
  value       = aws_ecr_repository.trades_service.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.traderx.name
}

output "tenant_id" {
  description = "Deployed tenant ID"
  value       = var.tenant_id
}
