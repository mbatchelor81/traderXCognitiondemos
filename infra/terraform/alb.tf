# --- AWS Load Balancer Controller ---
# The ALB controller will be installed as a post-apply step using kubectl/helm
# because the Devin-Migration-Service IAM user does not have iam:CreatePolicy permissions.
#
# Post-apply steps:
# 1. helm repo add eks https://aws.github.io/eks-charts
# 2. helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
#      -n kube-system \
#      --set clusterName=<cluster-name> \
#      --set serviceAccount.create=true \
#      --set region=<region> \
#      --set vpcId=<vpc-id>
#
# Alternatively, use a simple LoadBalancer service type for the frontend
# which creates a Classic Load Balancer without the ALB controller.

# Output the OIDC provider ARN for future IRSA configuration
output "oidc_provider_arn" {
  description = "OIDC provider ARN for IRSA"
  value       = aws_iam_openid_connect_provider.eks.arn
}
