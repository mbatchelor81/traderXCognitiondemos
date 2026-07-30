# Definition of Done

Every item traces back to a constraint in
[TARGET_ARCHITECTURE_CONSTRAINTS.md](../TARGET_ARCHITECTURE_CONSTRAINTS.md).
Process A owns single-tenancy, data isolation, and service extraction.
Process B owns containerization, Kubernetes, CI/CD, and infrastructure.

## Process A — single-tenant migration and service extraction

- [x] App runs in single-tenant mode only (§1) — no `CURRENT_TENANT`, `KNOWN_TENANTS`,
      `set_current_tenant()`, or `_runtime_state`
- [x] Tenant chosen at startup via `TENANT_ID` env var; the app fails fast when it is absent (§1)
- [x] Requests carrying a mismatched `X-Tenant-ID` header are rejected with `403` (§1)
- [x] Tenant-specific business rules resolved for the startup tenant only, not from a
      shared per-tenant config dict (§1)
- [x] Data isolation implemented — database per tenant, `DATABASE_URL` overridable (§2)
- [x] Two different `TENANT_ID` values produce two independent databases (§2)
- [x] Domain services extracted per the service boundary table (§7):
      account-service, trading-service, position-service, reference-data-service,
      people-service
- [x] Each service starts independently on its own port with `TENANT_ID` set (§7)
- [x] Cross-service communication uses HTTP APIs only — no shared DB access (§8)
- [x] Service dependency graph is a DAG — no circular dependencies between services (§8)
- [x] Each service has a `/health` endpoint returning
      `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}` (§3, §4)
- [x] Each service has an OpenAPI spec served at `/openapi.json` and `/docs` (§7)
- [x] Structured JSON logging with tenant and correlation IDs (§10)
- [x] Each service handles `SIGTERM` gracefully (§3, §4)
- [x] Each service has its own test suite and all suites pass
- [x] Cross-service integration test exists and passes
- [x] Frontend has no mutable tenant state — build-time `REACT_APP_TENANT_ID` only (§1)
- [x] Frontend API URLs point at the extracted service ports (§9 — replaced by the
      gateway/ALB in Process B)
- [x] `traderx-monolith/` retained with a deprecation notice in its README

## Process B — containerization, deployment, infrastructure

- [ ] Dockerfiles build successfully (§3)
- [ ] Images run as non-root with `HEALTHCHECK` instructions (§3)
- [ ] Kubernetes manifests or Helm charts valid, with readiness/liveness probes,
      resource limits, and HPAs (§4)
- [ ] GitHub Actions CI pipeline functional — lint, test, build, scan (§5)
- [ ] CD pipeline deploys to staging with a manual production gate (§5)
- [ ] Terraform validates and applies successfully (§6)
- [ ] API gateway / ingress routes by path prefix with TLS termination (§9)
- [ ] Prometheus `/metrics` endpoints and OpenTelemetry tracing wired up (§10)
- [ ] Smoke tests exist and pass against the deployed environment
