# Definition of Done — TraderX Migration

This checklist tracks every constraint from `TARGET_ARCHITECTURE_CONSTRAINTS.md` that applies to the TraderX migration. Items are checked off as each phase completes.

---

## Process A — Single-Tenant Migration and Service Extraction

### Single-Tenant Isolation (Section 1)
- [ ] App runs in single-tenant mode only — no runtime tenant switching
- [ ] Tenant chosen at startup via `TENANT_ID` environment variable
- [ ] Application crashes immediately if `TENANT_ID` is not set
- [ ] Requests with mismatched `X-Tenant-ID` header rejected with HTTP 403
- [ ] No shared in-memory state (`CURRENT_TENANT`, `_runtime_state`, `KNOWN_TENANTS` removed)
- [ ] Tenant-specific business rules loaded for current tenant only at startup
- [ ] Frontend uses build-time `REACT_APP_TENANT_ID` — no mutable tenant state

### Database-per-Tenant (Section 2)
- [ ] Data isolation implemented — each tenant gets its own database
- [ ] Database connection string incorporates `TENANT_ID`
- [ ] `DATABASE_URL` environment variable overridable for production
- [ ] `tenant_id` column no longer needed for row-level filtering
- [ ] Cross-tenant queries impossible by design

### Service Boundaries (Section 7)
- [ ] Domain services extracted per service boundary table in `TARGET_ARCHITECTURE_CONSTRAINTS.md`
- [ ] Account Service extracted — account CRUD, account user management
- [ ] Trading Service extracted — trade submission, validation, state machine
- [ ] Position Service extracted — position tracking, queries
- [ ] Reference Data Service extracted — stock ticker lookup
- [ ] People Service extracted — person directory, validation
- [ ] Each service owns its own data store (no shared database)
- [ ] Each service can be developed, deployed, and scaled independently

### No Cross-Service Database Access (Section 8)
- [ ] Cross-service communication uses HTTP APIs only (no shared DB access)
- [ ] No circular dependencies between services — dependency graph is a DAG
- [ ] Trade Service validates accounts via Account Service API (not direct DB query)
- [ ] Trade Service validates securities via Reference Data Service API (not CSV load)

### API Contracts
- [ ] Each service has a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- [ ] Each service has an OpenAPI spec accessible at `/docs`

### Observability (Section 10)
- [ ] Structured JSON logging with `tenant_id` and `service` fields
- [ ] Logs include correlation IDs

### Graceful Shutdown
- [ ] Each service handles `SIGTERM` gracefully — drains in-flight requests

### Testing
- [ ] Each service has its own test suite
- [ ] All service test suites pass with `TENANT_ID` set
- [ ] Integration test script exists and passes (cross-service HTTP calls)

### Frontend
- [ ] Frontend API URLs point at extracted service ports
- [ ] No tenant selector dropdown in UI
- [ ] No `TenantContext`, `fetchWithTenant`, or socket reconnect on tenant change

---

## Process B — Containerization, CI/CD, Infrastructure (Future)

### Containerized Services (Section 3)
- [ ] Dockerfiles build successfully for all services
- [ ] Images tagged with semantic version and commit SHA
- [ ] Containers run as non-root users
- [ ] Health check endpoints defined in Docker `HEALTHCHECK` instructions

### Kubernetes Deployable (Section 4)
- [ ] Kubernetes manifests or Helm charts valid
- [ ] Readiness and liveness probes configured
- [ ] Resource requests and limits defined
- [ ] Namespace isolation per environment

### CI/CD (Section 5)
- [ ] GitHub Actions CI pipeline functional
- [ ] Lint, test, build, security scan on every PR
- [ ] Docker image build and push on merge to main
- [ ] Automated staging deployment with smoke tests

### Infrastructure as Code (Section 6)
- [ ] Terraform validates and applies successfully
- [ ] VPC/VNet, subnets, security groups defined
- [ ] Kubernetes cluster (EKS/AKS) provisioned
- [ ] Database instances per tenant provisioned
- [ ] Container registry, load balancers, DNS configured

### API Gateway (Section 9)
- [ ] Central API gateway handles ingress traffic
- [ ] Path-based routing to appropriate services
- [ ] TLS termination, auth, rate limiting configured

### Observability — Metrics and Tracing (Section 10)
- [ ] Prometheus metrics endpoints exposed per service
- [ ] OpenTelemetry distributed tracing instrumented
- [ ] Smoke tests exist and pass against deployed infrastructure
