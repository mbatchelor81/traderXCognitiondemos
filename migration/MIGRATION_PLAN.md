# TraderX Migration Plan — Multi-Tenant Monolith to Single-Tenant Services

This document describes the migration of TraderX from a shared multi-tenant Python/FastAPI
monolith into single-tenant, independently deployable domain services, as required by
[TARGET_ARCHITECTURE_CONSTRAINTS.md](../TARGET_ARCHITECTURE_CONSTRAINTS.md).

---

## 1. Current State

### Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, FastAPI, SQLAlchemy, Socket.io (`python-socketio`), uvicorn |
| Database | SQLite, single file `traderx.db` |
| Frontend | React 18 + TypeScript (Create React App, `react-scripts`) |
| Tests | pytest (9 tests, green baseline), Jest / React Testing Library |
| Deployment | Manual `deploy.sh`, no containers, no CI/CD |

Backend lives in `traderx-monolith/` and serves everything on port 8000
(`python run.py`). Frontend lives in `web-front-end/react/` on port 3000
(`npm start`).

### Tenancy mechanism

Tenancy is header based and resolved per request:

- `traderx-monolith/app/middleware.py` — `TenantMiddleware.dispatch()` reads the
  `X-Tenant-ID` header and falls back to the module-level global
  `app.config.CURRENT_TENANT`, storing the result on `request.state.tenant_id`.
- `traderx-monolith/app/utils/helpers.py` — `get_tenant_from_request(request)` reads it
  back out; every route handler calls it and threads `tenant_id` through the service layer.
- `traderx-monolith/app/config.py` holds mutable global tenant state:
  - `CURRENT_TENANT` / `DEFAULT_TENANT` (`acme_corp`)
  - `KNOWN_TENANTS = ["acme_corp", "globex_inc", "initech"]` — appended to at runtime
  - `set_current_tenant(tenant_id)` — mutates the global and grows `KNOWN_TENANTS`
  - `_runtime_state` dict plus `get_runtime_state()` / `update_runtime_state()`
  - per-tenant business rules: `TENANT_MAX_ACCOUNTS`, `TENANT_ALLOWED_SIDES`,
    `TENANT_AUTO_SETTLE`
- Every module does `from app.config import *`, so the mutable globals are visible
  everywhere.

### Database layout

One SQLite file (`sqlite:///traderx.db`) shared by all tenants. Isolation is row level
via a `tenant_id` column on `accounts`, `account_users`, `trades`, and `positions`
(`app/models/*.py`). `app/seed.py` seeds all three demo tenants into the same file.

### Inter-module coupling

- **Circular dependency**: `app/services/account_service.py` ↔
  `app/services/trade_processor.py` (both use lazy in-function imports to break the cycle
  at import time — `get_trade_count_for_account()` and `get_account_display_name()`).
- **God service**: `app/services/trade_processor.py` (1046 lines) owns trade validation,
  the trade state machine, position mutation, account/user lookups, reference-data
  validation, tenant business rules, analytics, and Socket.io publishing.
- **Cross-domain queries**: `app/routes/accounts.py` `GET /account/{id}` queries the
  `positions` table directly; `app/routes/positions.py` and `app/routes/trades.py` run
  inline SQLAlchemy queries that bypass the service layer.
- **Reference data / people**: loaded from files by `app/utils/helpers.py`
  (`data/s-and-p-500-companies.csv`, `data/people.json`) and cached in module globals
  (`_stocks_cache`, `_people_cache`).
- **Frontend**: `TenantContext` / `TenantProvider`, a tenant selector dropdown in
  `App.tsx`, `fetchWithTenant()` injecting `X-Tenant-ID`, `reconnectSocket()` on tenant
  switch, and `useEffect(..., [tenant])` refetch dependencies in every hook.

### Deployment model

Single process, run by hand (`python run.py`), single SQLite file on the host, no
container image, no CI, no infrastructure as code.

---

## 2. Target State

Every running instance serves exactly **one** tenant.

- **Tenant at startup**: `TENANT_ID` is a required environment variable. Each service
  reads it once at import time and raises at startup if it is missing. There is no
  runtime tenant switching and no `set_current_tenant()`.
- **Request path**: the tenant middleware always resolves to the startup `TENANT_ID`.
  A request carrying `X-Tenant-ID` for a *different* tenant is rejected with `403`.
  A request with no header implicitly uses the startup tenant.
- **Database per tenant**: the default connection string is
  `sqlite:///<service>_{TENANT_ID}.db`, overridable with `DATABASE_URL` so production
  points at a tenant-specific managed database. Two `TENANT_ID`s can never share a
  database.
- **Service extraction**: five independently deployable services under `services/`,
  aligned with the boundaries in `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7.
- **Cross-service communication is HTTP only** — no service reads another service's
  tables. Service URLs come from environment variables.
- **Per-service `/health`**, OpenAPI spec, structured JSON logs with `tenant_id` and
  correlation IDs, and graceful `SIGTERM` handling.
- Process B then containerizes these services and deploys them to Kubernetes with
  CI/CD and Terraform.

### Extracted services

| Service | Port | Owns | Source moved from the monolith |
|---|---|---|---|
| `account-service` | 8001 | Account CRUD, account-user management, account validation | `app/models/account.py`, `app/services/account_service.py`, `app/routes/accounts.py` |
| `trading-service` | 8002 | Trade submission and validation, trade state machine, analytics, Socket.io events | `app/models/trade.py`, `app/services/trade_processor.py`, `app/services/analytics_service.py`, `app/routes/trades.py`, `app/routes/analytics.py`, Socket.io server from `app/main.py` |
| `position-service` | 8003 | Position tracking, queries, recalculation | `app/models/position.py`, `app/routes/positions.py`, position functions from `trade_processor.py` |
| `reference-data-service` | 8004 | S&P 500 ticker lookup | `app/routes/reference_data.py`, CSV helpers from `app/utils/helpers.py`, `data/s-and-p-500-companies.csv` |
| `people-service` | 8005 | Person directory and validation | `app/models/person.py`, `app/services/people_service.py`, `app/routes/people.py`, `data/people.json` |

### Cross-service dependency graph (a DAG — no cycles)

```
trading-service ──> account-service ──> people-service
       │    │                └────────> position-service
       │    └──────────────────────────> position-service
       └───────────────────────────────> reference-data-service
```

- `trading-service` validates the account (`GET /account/{id}`, `GET /accountuser/`) via
  `account-service`, validates the security via `reference-data-service`
  (`GET /stocks/{ticker}`), and applies position deltas via `position-service`
  (`POST /positions/apply`).
- `account-service` validates users via `people-service`
  (`GET /people/ValidatePerson`) and composes the portfolio summary from
  `position-service` (`GET /positions/{account_id}`).
- `position-service`, `reference-data-service`, and `people-service` have no outbound
  service dependencies.

The `account_service` ↔ `trade_processor` cycle is broken by giving trading-service the
single outbound edge: account-service no longer counts trades locally, and
trade_processor no longer imports account lookups — it calls the account-service API.

### Service URL environment variables

| Variable | Local default |
|---|---|
| `ACCOUNT_SERVICE_URL` | `http://localhost:8001` |
| `TRADING_SERVICE_URL` | `http://localhost:8002` |
| `POSITION_SERVICE_URL` | `http://localhost:8003` |
| `REFERENCE_DATA_SERVICE_URL` | `http://localhost:8004` |
| `PEOPLE_SERVICE_URL` | `http://localhost:8005` |

Every service additionally reads `TENANT_ID` (required), `DATABASE_URL`, `APP_HOST`,
`APP_PORT`, `LOG_LEVEL`, and `CORS_ORIGINS`.

### Frontend URL mapping

`web-front-end/react/src/env.ts` maps each API family to its owning service. The tenant
is a **build-time** variable, `REACT_APP_TENANT_ID`, baked into the bundle — it cannot
change at runtime.

| Config key | Target service | Local default |
|---|---|---|
| `account_service_url` | account-service | `http://<host>:8001` |
| `trade_service_url` | trading-service | `http://<host>:8002` |
| `trade_feed_url` (Socket.io) | trading-service | `http://<host>:8002` |
| `position_service_url` | position-service | `http://<host>:8003` |
| `reference_data_url` | reference-data-service | `http://<host>:8004` |
| `people_service_url` | people-service | `http://<host>:8005` |

Process B re-points these at the ALB / ingress hostname.

---

## 3. Phased Approach

| Phase | Scope | Owner |
|---|---|---|
| 1 | Migration documentation (`migration/MIGRATION_PLAN.md`, `migration/DEFINITION_OF_DONE.md`) | Process A |
| 2 | Single-tenant runtime — `TENANT_ID` required at startup, 403 on tenant mismatch, frontend tenant state removed | Process A |
| 3 | Data isolation — database per tenant | Process A |
| 4 | Service extraction — five services under `services/`, cross-service HTTP, `/health`, OpenAPI, JSON logs, SIGTERM | Process A |
| 5 | Containerization — Dockerfiles, image build and registry push | Process B |
| 6 | CI/CD — GitHub Actions build, test, scan, deploy | Process B |
| 7 | Infrastructure as Code — Terraform for VPC, EKS/AKS, databases, registry, load balancer | Process B |
| 8 | Smoke testing against the deployed environment | Process B |

---

## 4. Running Locally After Migration

```bash
# One service per shell, each with the tenant fixed at startup
TENANT_ID=acme_corp python services/account-service/run.py          # :8001
TENANT_ID=acme_corp python services/trading-service/run.py          # :8002
TENANT_ID=acme_corp python services/position-service/run.py         # :8003
TENANT_ID=acme_corp python services/reference-data-service/run.py   # :8004
TENANT_ID=acme_corp python services/people-service/run.py           # :8005

# Frontend — tenant is baked in at build time
cd web-front-end/react && REACT_APP_TENANT_ID=acme_corp npm start   # :3000
```

Cross-service integration test:

```bash
TENANT_ID=test_tenant python tests/integration/test_cross_service.py
```

The legacy monolith in `traderx-monolith/` is retained as a reference implementation and
is no longer the deployment target.
