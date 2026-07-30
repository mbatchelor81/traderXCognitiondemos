output "eks_cluster_name" {
  description = "Name of the EKS cluster."
  value       = aws_eks_cluster.this.name
}

output "eks_cluster_endpoint" {
  description = "Kubernetes API server endpoint."
  value       = aws_eks_cluster.this.endpoint
}

output "eks_cluster_oidc_issuer" {
  description = "OIDC issuer URL of the cluster, used for IRSA."
  value       = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

output "ecr_repository_urls" {
  description = "Map of workload name to ECR repository URL."
  value       = { for name, repo in aws_ecr_repository.this : name => repo.repository_url }
}

output "tenant_id" {
  description = "Tenant id injected into services as TENANT_ID."
  value       = var.tenant_id
}

output "tenant_slug" {
  description = "DNS-1123 safe form of the tenant id, used in resource and namespace names."
  value       = local.tenant_slug
}

output "kubernetes_namespace" {
  description = "Namespace the tenant overlay deploys into."
  value       = local.k8s_namespace
}

output "region" {
  description = "AWS region."
  value       = var.region
}

output "vpc_id" {
  description = "VPC id."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "Private subnet ids (EKS worker nodes, internal load balancers)."
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet ids (internet-facing ALB, NAT gateway)."
  value       = aws_subnet.public[*].id
}

output "service_ports" {
  description = "Container port per workload — must match Dockerfile EXPOSE and K8s containerPort/targetPort."
  value       = local.service_ports
}

output "update_kubeconfig_command" {
  description = "Convenience command to point kubectl at this cluster."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.this.name}"
}
