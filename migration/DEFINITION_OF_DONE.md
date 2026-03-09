# Definition of Done — TraderX Migration

This checklist covers every constraint from `TARGET_ARCHITECTURE_CONSTRAINTS.md` applicable to the TraderX migration. Items are grouped by process phase.

---

## Process A — Single-Tenant Migration & Service Extraction

### Single-Tenant Isolation (Section 1)
- [ ] App runs in single-tenant mode only
- [ ] Tenant chosen at startup via `TENANT_ID` env var
- [ ] Application crashes immediately if `TENANT_ID` is not set
- [ ] Requests with mismatched `X-Tenant-ID` header rejected with 403
- [ ] No shared in-memory tenant state (`CURRENT_TENANT`, `_runtime_state`, `KNOWN_TENANTS` removed)
- [ ] No mutable tenant switching at runtime (`set_current_tenant()` removed)
- [ ] Frontend uses build-time `REACT_APP_TENANT_ID` — no runtime tenant selector

### Data Isolation (Section 2)
- [ ] Data isolation implemented (database per tenant)
- [ ] Each `TENANT_ID` produces a separate database file
- [ ] `DATABASE_URL` env var overrides for production use
- [ ] Cross-tenant queries impossible by design

### Service Extraction (Section 7)
- [ ] Domain services extracted per service boundary table in `TARGET_ARCHITECTURE_CONSTRAINTS.md`
- [ ] `users-service` (port 8001): accounts, account-users, people directory
- [ ] `trades-service` (port 8002): trades, positions, reference data, Socket.io
- [ ] Each service requires `TENANT_ID` at startup (fail-fast)
- [ ] Each service has its own database (no shared DB access)

### Cross-Service Communication (Section 8)
- [ ] Cross-service communication uses HTTP APIs only (no shared DB access)
- [ ] No direct imports between service packages
- [ ] Inter-service URLs configurable via environment variables
- [ ] No circular dependencies between services

### API Contracts
- [ ] Each service has a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- [ ] Each service has an OpenAPI spec accessible at `/docs`

### Observability (Section 10)
- [ ] Structured JSON logging with `tenant_id` and `service` fields
- [ ] Each service includes correlation ID support

### Graceful Shutdown
- [ ] Each service handles `SIGTERM` gracefully (drain in-flight requests)

### Tests
- [ ] Each service has its own test suite (health, CRUD, cross-service mocks)
- [ ] Integration test script exists at `tests/integration/test_cross_service.py`
- [ ] All test suites pass with `TENANT_ID` set

### Documentation
- [ ] `migration/MIGRATION_PLAN.md` exists and is accurate
- [ ] `migration/DEFINITION_OF_DONE.md` exists (this file)
- [ ] Monolith README has deprecation notice pointing to `services/`

---

## Process B — Containerization, CI/CD, Infrastructure (Future)

### Containerization (Section 3)
- [ ] Dockerfiles build successfully for each service
- [ ] Images tagged with semantic version and commit SHA
- [ ] Containers run as non-root users
- [ ] Docker `HEALTHCHECK` instructions defined

### Kubernetes (Section 4)
- [ ] Kubernetes manifests or Helm charts valid
- [ ] Readiness and liveness probes configured
- [ ] Resource requests and limits defined
- [ ] Namespace isolation per environment

### CI/CD (Section 5)
- [ ] GitHub Actions CI pipeline functional
- [ ] Lint, test, build on every PR
- [ ] CD pipeline deploys to staging on merge to main
- [ ] Manual approval gate for production

### Infrastructure as Code (Section 6)
- [ ] Terraform validates and applies successfully
- [ ] VPC, K8s cluster, databases, container registry defined
- [ ] Remote state backend with locking
- [ ] Separate state per environment

### API Gateway (Section 9)
- [ ] Central API gateway routes requests to services
- [ ] TLS termination configured
- [ ] Rate limiting per tenant

### Observability — Metrics & Tracing (Section 10)
- [ ] Prometheus metrics endpoints (`/metrics`)
- [ ] OpenTelemetry distributed tracing
- [ ] Centralized log aggregation

### Smoke Tests
- [ ] Smoke tests exist and pass against deployed environment
