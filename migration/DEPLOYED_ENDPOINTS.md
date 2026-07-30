# Deployed Endpoints — tenant `acme_corp`

## Deployment status

**Not deployed.** `terraform apply` was never run, so no AWS resources exist for this
tenant yet.

The AWS credentials available to the session (`AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY`) are rejected by AWS:

```
$ aws sts get-caller-identity
An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation:
The security token included in the request is invalid.
```

Everything up to the AWS boundary is authored and verified — see
[Verified locally](#verified-locally). The URLs below are the *expected* addresses once
someone with valid credentials runs [Bringing the environment up](#bringing-the-environment-up);
they are placeholders until then, and this file should be updated with the real values
after the first apply.

| | |
|---|---|
| AWS region | `us-east-1` |
| Tenant id | `acme_corp` (slug `acme-corp` wherever underscores are illegal) |
| EKS cluster | `traderx-acme-corp` |
| Cluster endpoint | *(from `terraform output eks_cluster_endpoint`)* |
| Kubernetes namespace | `traderx-acme-corp` |
| Kubernetes version | 1.34 |
| ALB / Ingress URL | *(from `kubectl get ingress traderx -n traderx-acme-corp`)* |
| Frontend URL | the ALB root — `http://<alb-dns-name>/` |

### ECR repositories

`<account-id>.dkr.ecr.us-east-1.amazonaws.com/<repository>`:

| Workload | Repository |
|---|---|
| account-service | `traderx-account-service-acme-corp` |
| trading-service | `traderx-trading-service-acme-corp` |
| position-service | `traderx-position-service-acme-corp` |
| reference-data-service | `traderx-reference-data-service-acme-corp` |
| people-service | `traderx-people-service-acme-corp` |
| web-frontend | `traderx-web-frontend-acme-corp` |

## Routing

One ALB fronts everything on disjoint path prefixes, so the frontend and all five
services share a single origin. Routes are keyed on the prefixes the services actually
register — not on service names:

| Prefix | Service | Port |
|---|---|---|
| `/account`, `/accountuser` | account-service | 8001 |
| `/trade`, `/trades`, `/analytics`, `/socket.io` | trading-service | 8002 |
| `/positions` | position-service | 8003 |
| `/stocks` | reference-data-service | 8004 |
| `/people` | people-service | 8005 |
| `/svc/<slug>/health`, `/svc/<slug>/metrics` | the matching service | — |
| `/` (catch-all) | web-frontend | 8080 |

A bare `/health` is ambiguous behind a single hostname, so every service also answers on
`/svc/<slug>/health` and `/svc/<slug>/metrics`, where `<slug>` is one of `account`,
`trading`, `position`, `reference-data`, `people`. The smoke tests use those aliases.

`docker-compose.yml` reproduces exactly this routing locally with an nginx `gateway`
container on `http://localhost:8000`, so the same smoke suite runs against both.

## Observability

Each service exposes Prometheus metrics (`http_requests_total`,
`http_request_duration_seconds`, `http_request_errors_total`,
`http_requests_in_progress`, all labelled `service` and `tenant_id`) and emits JSON logs
carrying `service`, `tenant_id` and `correlation_id`.

OpenTelemetry is initialised in every service and injects `traceparent` on outbound
httpx calls. Spans are only exported when `OTEL_EXPORTER_OTLP_ENDPOINT` is set; with no
endpoint the pipeline is inert. **No tracing or metrics backend is provisioned by this
repository** — point `OTEL_EXPORTER_OTLP_ENDPOINT` at an OTLP collector (AWS Distro for
OpenTelemetry, Jaeger, Tempo) and scrape `/svc/<slug>/metrics` with Prometheus or the
CloudWatch agent to make use of them.

## Bringing the environment up

Requires valid AWS credentials for the demo account and `AWS_ROLE_ARN` set as a GitHub
Actions secret (an IAM role trusting this repository through the GitHub OIDC provider)
before `cd.yml` can run.

```bash
export AWS_REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 1. State backend (out-of-band: it cannot be managed by the state it stores)
aws s3api create-bucket --bucket "traderx-tfstate-${ACCOUNT_ID}" --region us-east-1
aws s3api put-bucket-versioning --bucket "traderx-tfstate-${ACCOUNT_ID}" \
  --versioning-configuration Status=Enabled
aws dynamodb create-table --table-name traderx-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1

# 2. Infrastructure (VPC, EKS 1.34, node group, ECR, ALB controller IAM) — 15-20 min
cd infra/terraform
sed -i "s/ACCOUNT_ID/${ACCOUNT_ID}/" backend.tf
terraform init
terraform plan -var="tenant_id=acme_corp" -var="environment=demo" -out=tfplan
terraform apply tfplan

# 3. AWS Load Balancer Controller (see infra/terraform/README.md for the Helm command)

# 4. Images
aws eks update-kubeconfig --name traderx-acme-corp --region us-east-1
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
for s in account-service trading-service position-service reference-data-service people-service; do
  docker build -t "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/traderx-${s}-acme-corp:latest" "services/${s}"
  docker push "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/traderx-${s}-acme-corp:latest"
done
# The frontend bakes its API origin in at build time, so it needs the ALB hostname.
# Deploy the backends first, read the Ingress address, then build and push the frontend
# with --build-arg REACT_APP_*_SERVICE_URL=http://<alb-dns-name>.

# 5. Workloads
kubectl apply -k k8s/overlays/tenant-acme_corp/
kubectl get ingress -n traderx-acme-corp   # -> ALB DNS name

# 6. Smoke tests
SMOKE_TEST_URL=http://<alb-dns-name> python -m pytest tests/smoke/ -v
```

## Verified locally

Run against `docker compose` on the Devin machine, not against AWS:

- All six images build; all six containers report Docker `HEALTHCHECK` healthy.
- `SMOKE_TEST_URL=http://localhost:8000 python -m pytest tests/smoke/ -v` — **24 passed**.
- `kubectl kustomize k8s/overlays/tenant-acme_corp/` renders; namespace
  `traderx-acme-corp`, `TENANT_ID=acme_corp`, no `PLACEHOLDER` left.
- `k8s/verify-port-contract.py` — `containerPort` == Service `port` == `targetPort` ==
  probe port for all six workloads.
- `terraform fmt -check -recursive` and `terraform validate` pass.
- 159 service unit tests pass with observability enabled.

## Teardown

```bash
kubectl delete -k k8s/overlays/tenant-acme_corp/
cd infra/terraform && terraform destroy -auto-approve \
  -var="tenant_id=acme_corp" -var="environment=demo"
```

The state bucket and the `traderx-tfstate-lock` DynamoDB table are created out-of-band
and are **not** removed by `terraform destroy`; delete them manually if you want the
account completely clean.

## Merge-to-deploy sequence

1. Merge the Process B PR into `feature/single-tenant-migration`.
2. Merge `feature/single-tenant-migration` into `main`.
3. The push to `main` triggers `.github/workflows/cd.yml`, which builds the six images,
   pushes them to ECR, runs `kubectl apply -k k8s/overlays/tenant-acme_corp/`, waits on
   every rollout, checks all pods are Running, and runs `tests/smoke/` against the ALB.

`cd.yml` also accepts `workflow_dispatch`, so the deployment can be exercised from any
branch without merging to `main`. Either path requires the Terraform infrastructure and
the ECR repositories to exist first, and `AWS_ROLE_ARN` to be set — the workflow
authenticates purely through OIDC and contains no static keys. Set the repository
variable `ALB_URL` once the ALB exists so the frontend bundle is built against it.
