# TraderX — Deployed Endpoints

## Live Deployment

| Resource | URL / Value |
|---|---|
| **ALB URL** | `http://traderx-demo-alb-1639291.us-east-1.elb.amazonaws.com` |
| **Frontend (React)** | `http://traderx-demo-alb-1639291.us-east-1.elb.amazonaws.com/` |
| **Users Service** | `http://traderx-demo-alb-1639291.us-east-1.elb.amazonaws.com/account/` |
| **Trades Service** | `http://traderx-demo-alb-1639291.us-east-1.elb.amazonaws.com/stocks/` |
| **AWS Region** | `us-east-1` |
| **ECS Cluster** | `traderx-acme_corp-demo` |
| **Tenant ID** | `acme_corp` |

## ECR Repositories

| Service | ECR Repository URL |
|---|---|
| users-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-users-service-acme_corp` |
| trades-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trades-service-acme_corp` |
| web-frontend | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-web-frontend-acme_corp` |

## ALB Routing Rules

| Path Pattern | Target Service |
|---|---|
| `/account/*`, `/accountuser/*`, `/people/*` | users-service (port 8001) |
| `/trade/*`, `/trades/*`, `/positions/*`, `/stocks/*` | trades-service (port 8002) |
| `/socket.io/*` | trades-service (port 8002) |
| `/*` (default) | web-frontend (port 8080) |

## Frontend Configuration

The React frontend API URLs are configured in `web-front-end/react/src/env.ts`. For the deployed build, the frontend uses `window.location.hostname` to construct API URLs, which resolves to the ALB hostname. The ALB path-based routing directs API requests to the correct backend service.

## Running Smoke Tests

```bash
# Install dependencies
pip install -r tests/smoke/requirements.txt

# Run against live ALB
SMOKE_TEST_URL=http://traderx-demo-alb-1639291.us-east-1.elb.amazonaws.com python -m pytest tests/smoke/ -v

# Run against local Docker Compose
TENANT_ID=acme_corp docker compose up -d
SMOKE_TEST_URL=http://localhost:8080 python -m pytest tests/smoke/ -v
docker compose down
```

## Observability

Each backend service exposes:
- **Prometheus metrics** at `/metrics` (request count, latency histogram, error count — labeled by service, tenant_id, method, path, status)
- **Structured JSON logs** with `timestamp`, `level`, `service`, `tenant_id`, and `correlation_id` fields
- **OpenTelemetry tracing** with `traceparent` header propagation between services

Observability backends (Prometheus server, Grafana, Jaeger/X-Ray) should be provisioned separately. Configure `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable to point at your tracing collector.

## Teardown

To destroy all AWS infrastructure:

```bash
cd infra/terraform
terraform destroy -auto-approve \
  -var="tenant_id=acme_corp" \
  -var="environment=demo"
```

**Note:** This will destroy the ECS cluster, ALB, VPC, ECR repositories, and all associated resources. The Terraform state S3 bucket and DynamoDB lock table are NOT destroyed (they are managed outside Terraform).
