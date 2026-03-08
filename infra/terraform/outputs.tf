output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "URL of the Application Load Balancer"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_users_service_url" {
  description = "ECR repository URL for users-service"
  value       = aws_ecr_repository.users_service.repository_url
}

output "ecr_trades_service_url" {
  description = "ECR repository URL for trades-service"
  value       = aws_ecr_repository.trades_service.repository_url
}

output "ecr_web_frontend_url" {
  description = "ECR repository URL for web-frontend"
  value       = aws_ecr_repository.web_frontend.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "tenant_id" {
  description = "Tenant ID for this deployment"
  value       = var.tenant_id
}
