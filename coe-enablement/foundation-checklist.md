# Foundation Layer Checklist

Track progress building the Devin COE foundation layer for TraderX. Each item maps to a concrete file, command, or configuration in this repository.

---

## Skills (target: 1 per repeatable task)

### Already Committed
- [x] `add-new-service` — Scaffold a new domain service module (model → service → routes → tests). File: `.agents/skills/add-new-service/SKILL.md` + `.windsurf/skills/add-new-service/SKILL.md`
- [x] `add-api-endpoint` — Add a REST endpoint to an existing route module. File: `.windsurf/skills/add-api-endpoint/SKILL.md`
- [x] `add-integration-test` — Write integration tests for API endpoints. File: `.windsurf/skills/add-integration-test/SKILL.md`
- [x] `add-observability-to-service` — Add structured logging, health checks, and request timing. File: `.windsurf/skills/add-observability-to-service/SKILL.md`
- [x] `testing-sentry-integration` — Test Sentry error monitoring end-to-end. File: `.agents/skills/testing-sentry-integration/SKILL.md`

### To Build
- [ ] `containerize-service` — Create a Dockerfile for a service following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §3 (non-root user, health check, minimal base image, no host dependencies)
- [ ] `add-service-ci` — Add a GitHub Actions CI job for a new service (lint, test, build Docker image) following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §5
- [ ] `add-tenant-config` — Add tenant-specific business rules to `app/config.py` (lines 76–92) and wire them into a service module via `app/middleware.py`
- [ ] `add-kubernetes-manifests` — Create K8s Deployment, Service, and HPA for a containerized service following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §4
- [ ] `add-inter-service-api-call` — Replace a cross-domain database query with an HTTP API call between services, following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §8

---

## Knowledge Notes (target: 1 per architectural decision / tribal knowledge)

### Already Committed
- [x] Circular dependency: `trade_processor.py` ↔ `account_service.py` — why it exists, how to avoid deepening it. File: `coe-enablement/knowledge-note.md`

### To Build
- [ ] Multi-tenant middleware pattern — how `TenantMiddleware` in `app/middleware.py` injects `tenant_id` from `X-Tenant-ID` header, and why every query must filter by it. Reference: `app/middleware.py`, `app/utils/helpers.py:get_tenant_from_request()`
- [ ] God service anti-pattern — why `trade_processor.py` (1046 lines) combines validation, processing, position calculation, and Socket.io publishing. How to safely extract functions without breaking the circular dependency. Reference: `LEGACY_ARCHITECTURE.md`
- [ ] `from app.config import *` everywhere — why every module uses wildcard config import, what breaks if you don't include it (missing `DEFAULT_TENANT`, `DATABASE_URL`, etc.), and why this is an intentional architectural smell. Reference: `app/config.py` docstring
- [ ] camelCase vs. snake_case boundary — Pydantic models use camelCase (matching React frontend), SQLAlchemy models use snake_case. The `to_dict()` method on each model handles the mapping. Reference: `app/models/trade.py:to_dict()`, `app/routes/trades.py:TradeOrderRequest`
- [ ] Test fixture architecture — `conftest.py` uses in-memory SQLite with `StaticPool`, `autouse=True` fixture creates/drops all tables per test, `get_db` dependency is overridden globally. Reference: `traderx-monolith/tests/conftest.py`
- [ ] Socket.io real-time push pattern — `trade_processor.py` publishes trade and position updates to room-scoped Socket.io channels (`/accounts/{id}/trades`). The `_sio` module-level reference is set once at startup by `main.py`. Reference: `app/main.py` lines 40–78, `app/services/trade_processor.py:set_socketio_server()`

---

## Playbooks (target: 1 per multi-step workflow)

### Already Committed
- [x] `extract-service` — Full service extraction: audit → scope → scaffold (sub-agent) → observability (sub-agent) → integration tests (sub-agent) → Dockerfile. File: `coe-enablement/playbook.md`

### To Build
- [ ] `onboard-new-tenant` — End-to-end tenant onboarding: add tenant config to `app/config.py`, seed reference data, create default accounts, run validation tests with `X-Tenant-ID` header
- [ ] `decompose-god-service` — Extract specific responsibility from `trade_processor.py` into a standalone service module (e.g., position calculation → `position_service.py`) without breaking the circular dependency
- [ ] `production-readiness-review` — Audit a service against all 10 sections of `TARGET_ARCHITECTURE_CONSTRAINTS.md` and produce a gap analysis with remediation steps

---

## CI/Automation

- [x] GitHub Actions CI: backend tests + frontend lint & build. File: `.github/workflows/ci.yml`
- [ ] Chisel batch script for observability instrumentation across all services. File: `coe-enablement/chisel-batch.sh`
- [ ] GitHub Action trigger for `extract-service` playbook via `workflow_dispatch` with `service_name` input
- [ ] Org-scoped knowledge configured for cross-repo sharing (Python best practices, testing pyramid, PR standards)
- [ ] Pre-commit hook for skill file validation (ensure no placeholder paths, verify referenced files exist)

---

## Scaling Milestones

- [ ] **Week 1:** 5 new skills committed, reviewed, and tested by invoking each against a real task
- [ ] **Week 2:** First playbook (`extract-service`) used in a real delivery sprint to extract a service
- [ ] **Week 2:** First sub-agent delegation working end-to-end (playbook Step 3 → Devin Cloud sub-session)
- [ ] **Week 3:** Chisel batch script validated — runs `add-observability` across all 5 target services in one invocation
- [ ] **Week 4:** First tenant onboarded using parameterized playbooks (new `KNOWN_TENANTS` entry + full service stack)
- [ ] **Month 2:** All 5 target services from `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7 extracted via playbooks
- [ ] **Month 2:** GitHub Action trigger operational — team can kick off service extractions from CI
- [ ] **Month 3:** 50+ tenant deployments using the same foundation layer, parameterized only by tenant config

---

## Quick Reference: File Locations

| Artifact Type | Path Pattern | Example |
|---|---|---|
| Devin Skills | `.agents/skills/{task-name}/SKILL.md` | `.agents/skills/add-new-service/SKILL.md` |
| Windsurf Skills | `.windsurf/skills/{task-name}/SKILL.md` | `.windsurf/skills/add-api-endpoint/SKILL.md` |
| Skill Templates | `.windsurf/skills/{task-name}/templates/` | `.windsurf/skills/add-new-service/templates/model.py.md` |
| Skill Examples | `.windsurf/skills/{task-name}/examples/` | `.windsurf/skills/add-api-endpoint/examples/get-endpoint.md` |
| Knowledge Notes | `coe-enablement/knowledge-note.md` or Devin Knowledge UI | `coe-enablement/knowledge-note.md` |
| Playbooks | `coe-enablement/playbook.md` or Devin Playbook UI | `coe-enablement/playbook.md` |
| Batch Scripts | `coe-enablement/chisel-batch.sh` | `coe-enablement/chisel-batch.sh` |
| Architecture Specs | Root directory | `TARGET_ARCHITECTURE_CONSTRAINTS.md`, `LEGACY_ARCHITECTURE.md` |
