# Definition of Done — TraderX Migration

This checklist tracks every constraint from `TARGET_ARCHITECTURE_CONSTRAINTS.md` that applies to the TraderX migration. Items are checked off as each phase completes.

---

## Process A — Single-Tenant Migration and Service Extraction

### Single-Tenant Isolation (Section 1)
- [x] App runs in single-tenant mode only — no runtime tenant switching
- [x] Tenant chosen at startup via `TENANT_ID` environment variable
- [x] Application crashes immediately if `TENANT_ID` is not set
- [x] Requests with mismatched `X-Tenant-ID` header rejected with HTTP 403
- [x] No shared in-memory state (`CURRENT_TENANT`, `_runtime_state`, `KNOWN_TENANTS` removed)
- [x] Tenant-specific business rules loaded for current tenant only at startup
- [x] Frontend uses build-time `REACT_APP_TENANT_ID` — no mutable tenant state

### Database-per-Tenant (Section 2)
- [x] Data isolation implemented — each tenant gets its own database
- [x] Database connection string incorporates `TENANT_ID`
- [x] `DATABASE_URL` environment variable overridable for production
- [x] `tenant_id` column no longer needed for row-level filtering
- [x] Cross-tenant queries impossible by design

### Service Boundaries (Section 7)
- [x] Domain services extracted per service boundary table in `TARGET_ARCHITECTURE_CONSTRAINTS.md`
- [x] Account Service extracted — account CRUD, account user management
- [x] Trading Service extracted — trade submission, validation, state machine
- [x] Position Service extracted — position tracking, queries
- [x] Reference Data Service extracted — stock ticker lookup
- [x] People Service extracted — person directory, validation
- [x] Each service owns its own data store (no shared database)
- [x] Each service can be developed, deployed, and scaled independently

### No Cross-Service Database Access (Section 8)
- [x] Cross-service communication uses HTTP APIs only (no shared DB access)
- [x] No circular dependencies between services — dependency graph is a DAG
- [x] Trade Service validates accounts via Account Service API (not direct DB query)
- [x] Trade Service validates securities via Reference Data Service API (not CSV load)

### API Contracts
- [x] Each service has a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- [x] Each service has an OpenAPI spec accessible at `/docs`

### Observability (Section 10)
- [x] Structured JSON logging with `tenant_id` and `service` fields
- [x] Logs include correlation IDs

### Graceful Shutdown
- [x] Each service handles `SIGTERM` gracefully — drains in-flight requests

### Testing
- [x] Each service has its own test suite
- [x] All service test suites pass with `TENANT_ID` set
- [x] Integration test script exists and passes (cross-service HTTP calls)

### Frontend
- [x] Frontend API URLs point at extracted service ports
- [x] No tenant selector dropdown in UI
- [x] No `TenantContext`, `fetchWithTenant`, or socket reconnect on tenant change

---

## Process B — Containerization, CI/CD, Infrastructure

### Containerized Services (Section 3)
- [x] Dockerfiles build successfully for all services
- [x] Images tagged with semantic version and commit SHA
- [x] Containers run as non-root users
- [x] Health check endpoints defined in Docker `HEALTHCHECK` instructions

### Kubernetes Deployable (Section 4)
- [x] Kubernetes manifests or Helm charts valid
- [x] Readiness and liveness probes configured
- [x] Resource requests and limits defined
- [x] Namespace isolation per environment

### CI/CD (Section 5)
- [x] GitHub Actions CI pipeline functional
- [x] Lint, test, build, security scan on every PR
- [x] Docker image build and push on merge to main
- [x] Automated staging deployment with smoke tests

### Infrastructure as Code (Section 6)
- [x] Terraform validates and applies successfully
- [x] VPC/VNet, subnets, security groups defined
- [x] Kubernetes cluster (EKS/AKS) provisioned
- [x] Database instances per tenant provisioned (SQLite per container)
- [x] Container registry, load balancers, DNS configured

### API Gateway (Section 9)
- [x] Central API gateway handles ingress traffic (ALB Ingress)
- [x] Path-based routing to appropriate services
- [ ] TLS termination, auth, rate limiting configured (deferred — demo environment)

### Observability — Metrics and Tracing (Section 10)
- [x] Prometheus metrics endpoints exposed per service (`/metrics`)
- [x] OpenTelemetry distributed tracing instrumented with W3C TraceContext propagation
- [x] Smoke tests exist and pass against deployed infrastructure (11/11 passing)
