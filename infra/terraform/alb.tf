# AWS Load Balancer Controller IAM Role for IRSA
resource "aws_iam_role" "alb_controller" {
  name = "traderx-${var.environment}-alb-controller"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
          "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

# ALB Controller IAM policy (AWS-managed)
resource "aws_iam_role_policy_attachment" "alb_controller" {
  policy_arn = "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
  role       = aws_iam_role.alb_controller.name
}

# Note: AWS Load Balancer Controller is installed as a post-apply step.
# After terraform apply, run:
#   helm repo add eks https://aws.github.io/eks-charts
#   helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
#     -n kube-system \
#     --set clusterName=<cluster-name> \
#     --set serviceAccount.create=true \
#     --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=<alb-controller-role-arn>
#
# Then apply the Ingress resource from k8s/base/ingress.yaml

# The Kubernetes Ingress manifest is maintained in k8s/base/ingress.yaml
# and deployed via kubectl apply -k. It uses ALB annotations for path-based routing:
#
# Path routing (based on actual service routes):
#   /account/*     -> account-service:8001
#   /accountuser/* -> account-service:8001
#   /trade/*       -> trading-service:8002
#   /trades/*      -> trading-service:8002
#   /positions/*   -> position-service:8003
#   /stocks/*      -> reference-data-service:8004
#   /people/*      -> people-service:8005
#   /*             -> web-frontend:18094
