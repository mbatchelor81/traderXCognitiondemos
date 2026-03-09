# AWS Load Balancer Controller IAM Role for Service Account (IRSA)
# The AWS Load Balancer Controller is installed as a post-apply step using Helm.
# This creates the IAM role that the controller's service account will assume.

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "alb_controller" {
  name = "traderx-${var.environment}-alb-controller"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
            "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  policy_arn = aws_iam_policy.alb_controller.arn
  role       = aws_iam_role.alb_controller.name
}

resource "aws_iam_policy" "alb_controller" {
  name = "traderx-${var.environment}-alb-controller-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcPeeringConnections",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeTags",
          "ec2:DescribeCoipPools",
          "ec2:GetCoipPoolUsage",
          "ec2:DescribeRouteTables",
          "elasticloadbalancing:*",
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:CreateTags",
          "ec2:DeleteTags",
          "iam:CreateServiceLinkedRole",
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "waf-regional:*",
          "wafv2:*",
          "shield:*",
          "iam:ListServerCertificates",
          "iam:GetServerCertificate",
        ]
        Resource = "*"
      }
    ]
  })
}

# Kubernetes Ingress resource for ALB path-based routing
# This is applied via kubectl after the ALB controller is installed.
# Route prefixes based on actual FastAPI service routes:
#   /account/*  -> account-service:8001
#   /trade/*    -> trading-service:8002
#   /positions/* -> position-service:8003
#   /trades/*   -> position-service:8003
#   /stocks/*   -> reference-data-service:8004
#   /people/*   -> people-service:8005
#   /health     -> account-service:8001 (default)

# The Ingress manifest is stored in k8s/base/ingress.yaml
# and applied with the Kustomize overlays.
