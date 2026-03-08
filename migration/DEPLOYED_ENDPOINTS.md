# TraderX — Deployed Endpoints

## Live Deployment

| Resource | Value |
|---|---|
| **ALB URL** | `http://traderx-demo-alb-315215138.us-east-1.elb.amazonaws.com` |
| **ECS Cluster** | `traderx-demo` |
| **AWS Region** | `us-east-1` |
| **Tenant ID** | `acme_corp` |
| **Environment** | `demo` |

## ECR Repository URLs

| Service | ECR URL |
|---|---|
| users-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-users-service-acme_corp` |
| trades-service | `599083837640.dkr.ecr.us-east-1.amazonaws.com/traderx-trades-service-acme_corp` |

## Service Endpoints (via ALB)

| Endpoint | Service | Description |
|---|---|---|
| `GET /health` | users-service | Health check |
| `GET /account/` | users-service | List accounts |
| `POST /account/` | users-service | Create account |
| `GET /account/{id}` | users-service | Get account by ID |
| `GET /accountuser/` | users-service | List account users |
| `POST /trade/` | trades-service | Submit a trade |
| `GET /trades/` | trades-service | List all trades |
| `GET /positions/` | trades-service | List all positions |
| `GET /stocks/` | trades-service | List reference data stocks |

## Running Smoke Tests

```bash
cd tests/smoke
pip install -r requirements.txt
SMOKE_TEST_URL=http://traderx-demo-alb-315215138.us-east-1.elb.amazonaws.com python -m pytest tests/smoke/ -v
```

## Observability

- **Prometheus metrics**: Each service exposes `/metrics` endpoint
- **Structured JSON logs**: All services emit JSON logs with `timestamp`, `level`, `service`, `tenant_id` fields
- **OpenTelemetry tracing**: Initialized in each service; configure `OTEL_EXPORTER_OTLP_ENDPOINT` env var to enable exporting
- **Observability backends** (Prometheus, Grafana, Jaeger) should be provisioned separately

## Teardown Instructions

To destroy all AWS infrastructure:

```bash
cd infra/terraform
terraform destroy -auto-approve -var="tenant_id=acme_corp" -var="environment=demo"
```

This will remove:
- ECS cluster and services
- ALB and target groups
- ECR repositories (and all images)
- VPC, subnets, security groups
- CloudWatch log groups
- IAM execution role

**Note:** The Terraform state S3 bucket (`traderx-terraform-state-599083837640`) and DynamoDB table (`traderx-terraform-locks`) are not managed by Terraform and must be deleted manually if no longer needed.
