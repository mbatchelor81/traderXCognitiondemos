# Deployed Endpoints — TraderX (Tenant: acme_corp)

## EKS Cluster

| Property | Value |
|---|---|
| **Cluster Name** | `traderx-acme-corp-demo` |
| **Cluster Endpoint** | `https://A219DB9E65FBF4A4D90796D1D6553FBD.gr7.us-east-1.eks.amazonaws.com` |
| **AWS Region** | `us-east-1` |
| **Kubernetes Namespace** | `traderx-acme-corp` |
| **Node Group** | `t3.medium`, min 1 / desired 2 / max 4 |

## ECR Repositories

| Service | ECR URL |
|---|---|
| users-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-users-service-acme_corp` |
| trades-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trades-service-acme_corp` |
| frontend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-frontend-acme_corp` |

## Service Endpoints (In-Cluster)

| Service | Port | Internal DNS |
|---|---|---|
| users-service | 8001 | `http://users-service.traderx-acme-corp.svc.cluster.local:8001` |
| trades-service | 8002 | `http://trades-service.traderx-acme-corp.svc.cluster.local:8002` |
| frontend | 8080 | `http://frontend.traderx-acme-corp.svc.cluster.local:8080` |

## Ingress / ALB

A Kubernetes Ingress resource (`traderx-ingress`) is configured with path-based routing:
- `/account/`, `/accounts/` → users-service
- `/trade/`, `/trades/`, `/positions/`, `/stocks/` → trades-service
- `/` → frontend

**Note:** The AWS Load Balancer Controller must be installed on the cluster for the ALB to be provisioned from the Ingress resource. If no external ALB address is shown, install the controller or use `kubectl port-forward` to access services directly.

### Accessing via port-forward

```bash
# Configure kubectl
aws eks update-kubeconfig --name traderx-acme-corp-demo --region us-east-1

# Port-forward each service
kubectl port-forward svc/users-service 8001:8001 -n traderx-acme-corp &
kubectl port-forward svc/trades-service 8002:8002 -n traderx-acme-corp &
kubectl port-forward svc/frontend 8080:8080 -n traderx-acme-corp &

# Test health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8080/health
```

## Observability

Each backend service exposes:
- **Prometheus metrics**: `GET /metrics` — request count, latency histogram, error rate (labeled by service, tenant_id, method, endpoint, status)
- **OpenTelemetry tracing**: Initialized with configurable OTLP exporter via `OTEL_EXPORTER_OTLP_ENDPOINT` env var. Defaults to no-op when not set.
- **Correlation ID**: `X-Correlation-ID` header propagated through all requests

Observability backends (Prometheus, Grafana, Jaeger/X-Ray) should be provisioned separately per environment requirements.

## Frontend Configuration

The frontend is containerized and deployed to EKS as an Nginx-based service. Backend API URLs are configured at the Kubernetes level via ConfigMap environment variables pointing to in-cluster service DNS.

## Running Smoke Tests

```bash
# Against local Docker Compose
TENANT_ID=acme_corp docker compose up -d
SMOKE_TEST_URL=http://localhost:8001 FRONTEND_PORT=80 python -m pytest tests/smoke/ -v
docker compose down

# Against live EKS (via port-forward)
kubectl port-forward svc/users-service 9001:8001 -n traderx-acme-corp &
kubectl port-forward svc/trades-service 9002:8002 -n traderx-acme-corp &
kubectl port-forward svc/frontend 9080:8080 -n traderx-acme-corp &
SMOKE_TEST_URL=http://localhost:9001 USERS_SERVICE_PORT=9001 TRADES_SERVICE_PORT=9002 FRONTEND_PORT=9080 python -m pytest tests/smoke/ -v
```

## Teardown Instructions

```bash
# 1. Remove Kubernetes resources
kubectl delete -k k8s/overlays/tenant-acme_corp/

# 2. Destroy Terraform infrastructure
cd infra/terraform
terraform destroy -auto-approve \
  -var="tenant_id=acme_corp" \
  -var="environment=demo" \
  -var="region=us-east-1"
```

**Warning:** `terraform destroy` will delete the EKS cluster, VPC, ECR repositories, and all associated resources. The Terraform state S3 bucket and DynamoDB lock table are NOT managed by Terraform and will persist.

## Merge-to-Deploy Sequence

1. Merge Process B PR → `feature/single-tenant-migration` branch
2. Merge `feature/single-tenant-migration` → `main` → triggers `cd.yml`
3. CD pipeline: builds images → pushes to ECR → deploys to EKS via kubectl → runs smoke tests
4. To validate deployment before merging to `main`, add the migration branch to the `cd.yml` trigger list (requires Terraform infrastructure to already exist)
