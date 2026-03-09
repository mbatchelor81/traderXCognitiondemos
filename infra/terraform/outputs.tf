output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "ecr_users_service_url" {
  description = "ECR repository URL for users-service"
  value       = aws_ecr_repository.users_service.repository_url
}

output "ecr_trades_service_url" {
  description = "ECR repository URL for trades-service"
  value       = aws_ecr_repository.trades_service.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "tenant_id" {
  description = "Deployed tenant ID"
  value       = var.tenant_id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "region" {
  description = "AWS region"
  value       = var.region
}
