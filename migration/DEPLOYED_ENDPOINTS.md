# Deployed Endpoints — TraderX Single-Tenant Demo

## Live Deployment

| Component | URL |
|---|---|
| **ALB Ingress** | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com` |
| Frontend (React) | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/` |
| Account Service | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/account/` |
| Trading Service | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/trade/` |
| Trade Blotter | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/trades/` |
| Position Service | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/positions/` |
| Reference Data | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/stocks/` |
| People Service | `http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com/people/` |

## AWS Infrastructure

| Resource | Value |
|---|---|
| AWS Account | `599083837640` |
| AWS Region | `us-east-1` |
| EKS Cluster Name | `traderx-demo` |
| EKS Cluster Version | `1.32` |
| EKS Node Group | 2x `t3.medium` (min 1, max 4) |
| K8s Namespace | `traderx-acme-corp` |
| Tenant ID | `acme_corp` |
| VPC ID | `vpc-0a726cc850a5a18d6` |

## ECR Repository URLs

| Service | ECR Repository |
|---|---|
| Account Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-account-service-acme_corp` |
| Trading Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trading-service-acme_corp` |
| Position Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-position-service-acme_corp` |
| Reference Data Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-reference-data-service-acme_corp` |
| People Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-people-service-acme_corp` |
| Web Frontend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-web-frontend-acme_corp` |

## Running Smoke Tests

```bash
# Against live deployment
SMOKE_TEST_URL=http://k8s-traderxa-traderxi-dd2b4398d0-1308754558.us-east-1.elb.amazonaws.com \
  python -m pytest tests/smoke/ -v

# Against local Docker Compose
TENANT_ID=acme_corp docker compose up -d
SMOKE_TEST_URL=http://localhost:18094 python -m pytest tests/smoke/test_health.py -v
docker compose down
```

## Teardown Instructions

To remove the deployed workloads and infrastructure:

```bash
# 1. Delete Kubernetes workloads
kubectl delete -k k8s/overlays/tenant-acme_corp/

# 2. Uninstall ALB controller
helm uninstall aws-load-balancer-controller -n kube-system

# 3. Destroy Terraform infrastructure
cd infra/terraform
terraform destroy -auto-approve \
  -var="tenant_id=acme_corp" \
  -var="environment=demo" \
  -var="region=us-east-1"
```

> **Warning:** `terraform destroy` will delete the EKS cluster, VPC, ECR repositories, and all associated resources. This action is irreversible.

## Merge-to-Deploy Sequence

1. Merge Process B PR into `feature/single-tenant-migration`
2. Merge `feature/single-tenant-migration` into `main`
3. Push to `main` triggers `cd.yml`:
   - Builds Docker images for all services
   - Pushes images to ECR (tagged with commit SHA + `latest`)
   - Deploys to EKS via `kubectl apply -k k8s/overlays/tenant-acme_corp/`
   - Waits for rollouts to complete
   - Runs smoke tests against the ALB URL
4. If validating before merging to `main`: the `cd.yml` trigger list includes `feature/single-tenant-migration` (requires Terraform infrastructure to already exist)

## Observability

- **Metrics:** Each service exposes a `/metrics` endpoint returning Prometheus-compatible metrics (request count, latency histogram, error rate)
- **Structured Logging:** All services emit JSON-formatted logs with `timestamp`, `level`, `service`, `tenant_id`, and `correlation_id` fields
- **Tracing:** OpenTelemetry tracing initialized in each service with W3C TraceContext (`traceparent`) header propagation. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to configure the trace exporter (AWS X-Ray, Jaeger, etc.)
- **Monitoring backends:** Prometheus + Grafana and a tracing backend (Jaeger or AWS X-Ray) should be provisioned separately for production use
