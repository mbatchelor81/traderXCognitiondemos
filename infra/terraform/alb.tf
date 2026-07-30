# AWS Load Balancer Controller (IRSA role + ServiceAccount + Helm release).
#
# This file installs the *controller* only. The Ingress object that actually causes
# an ALB to be provisioned lives in k8s/base/ingress.yaml (authored by another
# child session) and is applied separately with:
#
#   kubectl apply -k k8s/overlays/acme-corp
#
# Ordering matters: the controller must be installed and its pods healthy before
# the Ingress is applied (or reconciled), otherwise the Ingress stays pending with
# no ADDRESS and no ALB is created. The controller discovers subnets via the
# kubernetes.io/role/elb and kubernetes.io/cluster/<name> tags set in vpc.tf.

locals {
  alb_controller_service_account = "aws-load-balancer-controller"
  alb_controller_namespace       = "kube-system"
}

# IAM policy document is the official upstream policy, vendored to
# infra/terraform/alb-controller-policy.json (kubernetes-sigs/aws-load-balancer-controller
# v2.8.2 docs/install/iam_policy.json).
resource "aws_iam_policy" "alb_controller" {
  name        = "${local.name_prefix}-alb-controller"
  description = "IAM policy for the AWS Load Balancer Controller in ${local.name_prefix}"
  policy      = file("${path.module}/alb-controller-policy.json")

  tags = local.common_tags
}

data "aws_iam_policy_document" "alb_controller_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${local.alb_controller_namespace}:${local.alb_controller_service_account}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "alb_controller" {
  name               = "${local.name_prefix}-alb-controller-role"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume_role.json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "alb_controller" {
  role       = aws_iam_role.alb_controller.name
  policy_arn = aws_iam_policy.alb_controller.arn
}

resource "kubernetes_service_account" "alb_controller" {
  metadata {
    name      = local.alb_controller_service_account
    namespace = local.alb_controller_namespace

    labels = {
      "app.kubernetes.io/name"      = local.alb_controller_service_account
      "app.kubernetes.io/component" = "controller"
    }

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.alb_controller.arn
    }
  }

  depends_on = [aws_eks_node_group.default]
}

resource "helm_release" "alb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "1.8.1"
  namespace  = local.alb_controller_namespace

  set {
    name  = "clusterName"
    value = aws_eks_cluster.this.name
  }

  set {
    name  = "region"
    value = var.region
  }

  set {
    name  = "vpcId"
    value = aws_vpc.this.id
  }

  set {
    name  = "serviceAccount.create"
    value = "false"
  }

  set {
    name  = "serviceAccount.name"
    value = local.alb_controller_service_account
  }

  depends_on = [
    kubernetes_service_account.alb_controller,
    aws_iam_role_policy_attachment.alb_controller,
    aws_eks_addon.coredns,
  ]
}
