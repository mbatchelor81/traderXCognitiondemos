# Definition of Done — TraderX Migration

This checklist covers every constraint from `TARGET_ARCHITECTURE_CONSTRAINTS.md` applicable to the TraderX migration. Items are grouped by process phase.

---

## Process A — Single-Tenant Migration & Service Extraction

### Single-Tenant Isolation (Section 1)
- [x] App runs in single-tenant mode only
- [x] Tenant chosen at startup via `TENANT_ID` env var
- [x] Application crashes immediately if `TENANT_ID` is not set
- [x] Requests with mismatched `X-Tenant-ID` header rejected with 403
- [x] No shared in-memory tenant state (`CURRENT_TENANT`, `_runtime_state`, `KNOWN_TENANTS` removed)
- [x] No mutable tenant switching at runtime (`set_current_tenant()` removed)
- [x] Frontend uses build-time `REACT_APP_TENANT_ID` — no runtime tenant selector

### Data Isolation (Section 2)
- [x] Data isolation implemented (database per tenant)
- [x] Each `TENANT_ID` produces a separate database file
- [x] `DATABASE_URL` env var overrides for production use
- [x] Cross-tenant queries impossible by design

### Service Extraction (Section 7)
- [x] Domain services extracted per service boundary table in `TARGET_ARCHITECTURE_CONSTRAINTS.md`
- [x] `users-service` (port 8001): accounts, account-users, people directory
- [x] `trades-service` (port 8002): trades, positions, reference data, Socket.io
- [x] Each service requires `TENANT_ID` at startup (fail-fast)
- [x] Each service has its own database (no shared DB access)

### Cross-Service Communication (Section 8)
- [x] Cross-service communication uses HTTP APIs only (no shared DB access)
- [x] No direct imports between service packages
- [x] Inter-service URLs configurable via environment variables
- [x] No circular dependencies between services

### API Contracts
- [x] Each service has a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- [x] Each service has an OpenAPI spec accessible at `/docs`

### Observability (Section 10)
- [x] Structured JSON logging with `tenant_id` and `service` fields
- [x] Each service includes correlation ID support

### Graceful Shutdown
- [x] Each service handles `SIGTERM` gracefully (drain in-flight requests)

### Tests
- [x] Each service has its own test suite (health, CRUD, cross-service mocks)
- [x] Integration test script exists at `tests/integration/test_cross_service.py`
- [x] All test suites pass with `TENANT_ID` set

### Documentation
- [x] `migration/MIGRATION_PLAN.md` exists and is accurate
- [x] `migration/DEFINITION_OF_DONE.md` exists (this file)
- [x] Monolith README has deprecation notice pointing to `services/`

---

## Process B — Containerization, CI/CD, Infrastructure (Future)

### Containerization (Section 3)
- [x] Dockerfiles build successfully for each service
- [x] Images tagged with commit SHA and `latest`
- [x] Containers run as non-root users
- [x] Docker `HEALTHCHECK` instructions defined

### Kubernetes (Section 4)
- [x] Kubernetes manifests (Kustomize) valid for all services
- [x] Readiness and liveness probes configured
- [x] Resource requests and limits defined
- [x] Namespace isolation per tenant (`traderx-acme-corp`)

### CI/CD (Section 5)
- [x] GitHub Actions CI pipeline functional (`.github/workflows/ci.yml`)
- [x] Lint, test, build on every PR
- [x] CD pipeline deploys to EKS on merge to main (`.github/workflows/cd.yml`)
- [x] Smoke tests in CD pipeline

### Infrastructure as Code (Section 6)
- [x] Terraform validates and applies successfully
- [x] VPC, EKS cluster, ECR repositories defined
- [x] Remote state backend with locking (S3 + DynamoDB)
- [x] Separate state per environment

### API Gateway (Section 9)
- [x] Kubernetes Ingress routes requests to services via path-based routing
- [ ] TLS termination configured (requires ACM certificate and domain)
- [ ] Rate limiting per tenant (requires API Gateway or Ingress controller add-on)

### Observability — Metrics & Tracing (Section 10)
- [x] Prometheus metrics endpoints (`/metrics`) on each service
- [x] OpenTelemetry distributed tracing initialized in each service
- [x] Correlation ID propagation via `X-Correlation-ID` header
- [ ] Centralized log aggregation (requires CloudWatch or ELK stack)

### Smoke Tests
- [x] Smoke tests exist and pass against deployed environment
- [x] Health checks for all 3 services
- [x] End-to-end core flow test (create account, submit trade, verify position)
- [x] Correlation ID propagation test
- [x] Tenant isolation test
