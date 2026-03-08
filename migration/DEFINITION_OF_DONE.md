# TraderX Migration — Definition of Done

This checklist covers every constraint from `TARGET_ARCHITECTURE_CONSTRAINTS.md` applicable to the TraderX migration. Items are organized by Process A (code migration) and Process B (infrastructure).

---

## Process A — Single-Tenant Migration and Service Extraction

### Single-Tenant Isolation (Section 1)
- [x] App runs in single-tenant mode only
- [x] Tenant chosen at startup via `TENANT_ID` env var
- [x] Application fails fast if `TENANT_ID` is not set
- [x] Requests with mismatched `X-Tenant-ID` header are rejected with 403
- [x] No shared mutable tenant state (`CURRENT_TENANT`, `KNOWN_TENANTS`, `set_current_tenant()` removed)
- [x] No shared `_runtime_state` dict mutated from multiple modules
- [x] Tenant-specific business rules loaded for current tenant only at startup

### Data Isolation (Section 2)
- [x] Data isolation implemented (database per tenant)
- [x] Two different `TENANT_ID` values produce two separate databases
- [x] `tenant_id` column no longer needed for row-level filtering (isolation at infrastructure level)
- [x] `DATABASE_URL` env var overrides tenant-specific database for production use

### Service Extraction (Section 7)
- [x] Domain services extracted per user-specified boundaries (users, trades)
- [x] Each service owns its own data store (no shared database)
- [x] Each service can be started independently on its own port
- [x] Each service requires `TENANT_ID` at startup (fail-fast)

### Cross-Service Communication (Section 8)
- [x] Cross-service communication uses HTTP APIs only (no shared DB access)
- [x] No direct imports between service packages
- [x] No circular dependencies between services
- [x] Inter-service URLs configured via environment variables

### API Contracts
- [x] Each service has a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- [x] Each service has an OpenAPI spec accessible at `/docs`

### Observability (Section 10)
- [x] Structured JSON logging with tenant and correlation IDs
- [x] Each service includes `tenant_id` and `service` fields in log output

### Graceful Shutdown
- [x] Each service handles SIGTERM gracefully (drain in-flight requests)

### Testing
- [x] Each service has its own test suite
- [x] All service test suites pass with `TENANT_ID` set
- [x] Cross-service HTTP call stubs/mocks in tests

### Legacy Reference
- [x] Original monolith directory preserved (not deleted)
- [x] Monolith README has deprecation notice pointing to `services/`

---

## Process B — Containerization, CI/CD, and Infrastructure (Future)

### Containerization (Section 3)
- [ ] Dockerfiles build successfully for each service
- [ ] Images tagged with semantic version and commit SHA
- [ ] Containers run as non-root users
- [ ] Health check endpoints defined in Docker `HEALTHCHECK` instructions

### Kubernetes (Section 4)
- [ ] Kubernetes manifests or Helm charts valid
- [ ] Each service has Deployment, Service, and HorizontalPodAutoscaler
- [ ] Readiness and liveness probes configured
- [ ] Resource requests and limits defined
- [ ] Namespaces for environment isolation

### CI/CD (Section 5)
- [ ] GitHub Actions CI pipeline functional
- [ ] Lint, test, build, and deploy stages defined
- [ ] Coverage thresholds enforced
- [ ] Manual approval gate for production

### Infrastructure as Code (Section 6)
- [ ] Terraform validates and applies successfully
- [ ] Database-per-tenant provisioning automated
- [ ] Remote state backend configured

### API Gateway (Section 9)
- [ ] API gateway routes traffic to services by path prefix
- [ ] TLS termination configured
- [ ] Rate limiting per tenant

### Observability — Metrics and Tracing (Section 10)
- [ ] Prometheus `/metrics` endpoint on each service
- [ ] OpenTelemetry distributed tracing instrumented
- [ ] Grafana dashboards for visualization

### Smoke Testing
- [ ] Smoke tests exist and pass against deployed services
- [ ] End-to-end trade lifecycle verified in staging
