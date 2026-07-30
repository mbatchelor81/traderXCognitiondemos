# TraderX Terraform — AWS EKS (tenant `acme_corp`)

Implements TARGET_ARCHITECTURE_CONSTRAINTS.md §6 for a single tenant: VPC, EKS
cluster, managed node group, ECR repositories, IRSA and the AWS Load Balancer
Controller.

| File | Contents |
|---|---|
| `backend.tf` | S3 remote state + DynamoDB state locking |
| `providers.tf` | `aws`, `kubernetes`, `helm`, `tls` providers |
| `variables.tf` | Tenant/env/region/cluster inputs, the port contract, derived `locals` |
| `vpc.tf` | VPC `10.0.0.0/16`, 2 public + 2 private subnets, IGW, single NAT, routes |
| `ecr.tf` | One repository per workload, scan-on-push, keep-last-10 lifecycle policy |
| `eks.tf` | Control plane (K8s 1.34), node group, IRSA OIDC provider, core addons, access entry |
| `alb.tf` | ALB controller IRSA role, ServiceAccount and Helm release |
| `alb-controller-policy.json` | Official upstream IAM policy (aws-load-balancer-controller v2.8.2) |
| `outputs.tf` | Cluster/VPC/ECR outputs and the `update-kubeconfig` command |

## Naming

`TENANT_ID` stays `acme_corp` (the value services read at startup — every service
fails fast without it). AWS and Kubernetes DNS-1123 names cannot contain
underscores, so all derived names use the slug:

- `tenant_slug` = `acme-corp`
- `name_prefix` = `traderx-acme-corp` (EKS cluster name, IAM role prefix)
- Kubernetes namespace = `traderx-acme-corp`
- ECR repositories = `traderx-<workload>-acme-corp`

## `ACCOUNT_ID` in `backend.tf`

Terraform backend blocks cannot use variables, so the state bucket name contains
the literal token `ACCOUNT_ID`. It is substituted at init time:

```bash
sed -i "s/ACCOUNT_ID/$(aws sts get-caller-identity --query Account --output text)/" backend.tf
terraform init
```

The bucket `traderx-tfstate-<account id>` and the lock table
`traderx-tfstate-lock` must already exist; they are created out-of-band by the
bootstrap process and are deliberately not managed here (a state store managed by
its own state is a chicken-and-egg problem).

## Apply order

Terraform's dependency graph handles ordering within a single apply. The intended
order is:

1. `terraform init` (after the `ACCOUNT_ID` substitution above).
2. `terraform apply` — VPC → ECR → EKS control plane → OIDC provider → node group →
   addons (`coredns` waits for the node group) → ALB controller IAM role →
   ServiceAccount → Helm release.
3. `aws eks update-kubeconfig --region us-east-1 --name traderx-acme-corp`
   (also emitted as the `update_kubeconfig_command` output).
4. Build and push images to the ECR repositories in the `ecr_repository_urls`
   output.
5. Apply the Kubernetes manifests: `kubectl apply -k k8s/overlays/acme-corp`.
   The Ingress in `k8s/base/ingress.yaml` is **not** managed by Terraform. Wait
   until the `aws-load-balancer-controller` pods in `kube-system` are Ready before
   applying it, otherwise the Ingress stays pending with no ALB address.

## Port contract

| Workload | Port |
|---|---|
| account-service | 8001 |
| trading-service | 8002 |
| position-service | 8003 |
| reference-data-service | 8004 |
| people-service | 8005 |
| web-frontend | 8080 |

These are exposed as Terraform variables and the `service_ports` output so the
Dockerfile `EXPOSE`, Kubernetes `containerPort` and Service `targetPort` values can
be cross-checked against a single source of truth.

## Local verification (no AWS access needed)

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
```

## Demo-only tradeoffs

- **Single NAT gateway** shared by both AZs — cheaper, but a single point of
  failure. Production should use one NAT per AZ with per-AZ private route tables.
- **`force_delete = true`** on ECR repositories so `terraform destroy` works with
  images still present.
- **Public EKS API endpoint** enabled for convenience; restrict
  `public_access_cidrs` or disable it for production.
