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
- [ ] Each service includes correlation ID support

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
