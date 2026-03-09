output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for the EKS cluster"
  value       = aws_eks_cluster.main.endpoint
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for each service"
  value = {
    for service, repo in aws_ecr_repository.services : service => repo.repository_url
  }
}

output "tenant_id" {
  description = "Tenant ID used for this deployment"
  value       = var.tenant_id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "alb_controller_role_arn" {
  description = "IAM role ARN for the AWS Load Balancer Controller"
  value       = aws_iam_role.alb_controller.arn
}
