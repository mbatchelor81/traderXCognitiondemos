# Deployed Endpoints — TraderX Demo Environment

## Live Deployment

| Resource | URL / Value |
|---|---|
| **ALB URL** | `http://traderx-demo-alb-1557790683.us-east-1.elb.amazonaws.com` |
| **Frontend** | `http://traderx-demo-alb-1557790683.us-east-1.elb.amazonaws.com/` |
| **Users Service** | Routes: `/account/*`, `/accountuser/*`, `/people/*` |
| **Trades Service** | Routes: `/trade/*`, `/trades/*`, `/positions/*`, `/stocks/*`, `/socket.io/*` |

## AWS Resources

| Resource | Value |
|---|---|
| **AWS Region** | `us-east-1` |
| **AWS Account** | `599083837640` |
| **ECS Cluster** | `traderx-demo` |
| **Tenant ID** | `acme_corp` |

### ECR Repositories

| Service | Repository URL |
|---|---|
| Users Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-users-service-acme_corp` |
| Trades Service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trades-service-acme_corp` |
| Frontend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-frontend-acme_corp` |

### ECS Services

| Service | Desired | Running | Port |
|---|---|---|---|
| `traderx-users-service` | 1 | 1 | 8001 |
| `traderx-trades-service` | 1 | 1 | 8002 |
| `traderx-frontend` | 1 | 1 | 80 |

## Frontend Configuration

The React frontend is containerized (multi-stage: Node.js build + nginx serve) and deployed as an ECS service behind the ALB. The frontend's `env.ts` uses same-origin API calls by default, which works correctly when served behind the ALB with path-based routing. No manual configuration is needed.

To override the API URL at build time, set `REACT_APP_API_URL` environment variable.

## Observability

- **Prometheus Metrics**: Each service exposes `/metrics` endpoint (Prometheus format)
- **Structured Logging**: JSON logs with `timestamp`, `level`, `service`, `tenant_id`, `correlation_id`
- **OpenTelemetry Tracing**: Initialized in each service; configure `OTEL_EXPORTER_OTLP_ENDPOINT` to enable export

Observability backends (Prometheus, Grafana, Jaeger, etc.) should be provisioned separately and configured to scrape/receive from these endpoints.

## Running Smoke Tests

```bash
# Against local Docker Compose
TENANT_ID=acme_corp docker compose up -d
SMOKE_TEST_URL=http://localhost:80 python -m pytest tests/smoke/ -v
docker compose down

# Against live ALB
SMOKE_TEST_URL=http://traderx-demo-alb-1557790683.us-east-1.elb.amazonaws.com python -m pytest tests/smoke/ -v
```

## Teardown Instructions

To destroy all AWS infrastructure:

```bash
cd infra/terraform
terraform destroy -auto-approve -var="tenant_id=acme_corp" -var="environment=demo"
```

**Warning:** This will delete all ECS services, ALB, ECR repositories (including images), VPC, and associated resources. The Terraform state S3 bucket and DynamoDB lock table are NOT managed by Terraform and must be deleted manually if no longer needed.

## Merge-to-Deploy Sequence

1. **Merge Process B PR** → `feature/single-tenant-migration`
2. **Merge migration branch** → `main` → triggers `cd.yml`
   - Builds Docker images
   - Pushes to ECR
   - Deploys to demo environment (ECS force-deploy)
   - Waits for services to stabilize
   - Runs smoke tests
3. If the team wants to validate deployment before merging to `main`, add the migration branch to the `cd.yml` trigger list (requires Terraform infrastructure to already exist).
