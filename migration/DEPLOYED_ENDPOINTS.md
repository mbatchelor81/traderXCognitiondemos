# Deployed Endpoints — TraderX Single-Tenant Migration

## Live Deployment

| Resource | Value |
|---|---|
| **ALB/Ingress URL** | `http://k8s-traderxt-traderxi-9163f83401-378758816.us-east-1.elb.amazonaws.com` |
| **EKS Cluster Name** | `traderx-demo` |
| **EKS Cluster Endpoint** | `https://013B55F1BF6B0B7B32F350FBDB11EAEA.gr7.us-east-1.eks.amazonaws.com` |
| **AWS Region** | `us-east-1` |
| **Tenant ID** | `test_tenant` |
| **K8s Namespace** | `traderx-test_tenant` |

## ECR Repository URLs

| Service | ECR Repository |
|---|---|
| Account Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-account-service-test_tenant` |
| Trading Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trading-service-test_tenant` |
| Position Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-position-service-test_tenant` |
| Reference Data Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-reference-data-service-test_tenant` |
| People Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-people-service-test_tenant` |

## ALB Route Map

| Path Prefix | Target Service | Port |
|---|---|---|
| `/account` | account-service | 8001 |
| `/accountuser` | account-service | 8001 |
| `/trade` | trading-service | 8002 |
| `/positions` | position-service | 8003 |
| `/trades` | position-service | 8003 |
| `/stocks` | reference-data-service | 8004 |
| `/people` | people-service | 8005 |
| `/health` | account-service | 8001 |

## Frontend Configuration Status

The React frontend (`web-front-end/react/`) needs manual configuration to point at the ALB URL. Update `src/env.ts` with the ALB URL for each backend service. The frontend is **not** containerized or deployed as part of this migration — it should be built and served separately (e.g., via S3 + CloudFront or a separate container).

## How to Run Smoke Tests

```bash
# Install smoke test dependencies
pip install -r tests/smoke/requirements.txt

# Run against local Docker Compose
TENANT_ID=test_tenant docker compose up -d
python -m pytest tests/smoke/ -v
docker compose down

# Run against live ALB deployment
SMOKE_TEST_URL=http://k8s-traderxt-traderxi-9163f83401-378758816.us-east-1.elb.amazonaws.com \
  python -m pytest tests/smoke/ -v
```

## Teardown Instructions

To tear down the deployed environment:

```bash
# 1. Delete Kubernetes resources
kubectl delete -k k8s/overlays/tenant-test_tenant/

# 2. Destroy Terraform infrastructure
cd infra/terraform
terraform destroy -auto-approve \
  -var="tenant_id=test_tenant" \
  -var="environment=demo"
```

> **Warning:** `terraform destroy` will delete the EKS cluster, VPC, ECR repositories, and all associated resources. This is irreversible.

## Merge-to-Deploy Sequence

1. **Merge Process B PR** → `feature/single-tenant-migration` branch
2. **Merge migration branch** → `main` → triggers `cd.yml`
3. `cd.yml` pipeline: builds images → pushes to ECR → deploys to EKS via `kubectl apply -k` → runs smoke tests
4. To validate deployment before merging to `main`, add the migration branch to the `cd.yml` trigger list (requires Terraform infrastructure to already exist)

## Observability

Each service exposes:
- **`/metrics`** — Prometheus-format metrics (request count, latency histogram, error rate)
- **Structured JSON logs** — with `timestamp`, `level`, `service`, `tenant_id`, `correlation_id`
- **OpenTelemetry tracing** — configured via `OTEL_EXPORTER_OTLP_ENDPOINT` env var

Observability backends (Prometheus, Grafana, Jaeger) should be provisioned separately per environment requirements.
