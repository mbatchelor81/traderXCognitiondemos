# Migration Plan — TraderX: Multi-Tenant to Single-Tenant

## Current State

### Tech Stack
- **Backend**: Python 3.11+ / FastAPI monolith (`traderx-monolith/`) running on uvicorn at port 8000
- **Frontend**: React 18 (Create React App) at `web-front-end/react/`, port 18094
- **Database**: SQLite via SQLAlchemy ORM — single file `traderx.db`
- **Real-time**: Socket.io (python-socketio) embedded in the ASGI process
- **Deployment**: Manual via `deploy.sh` — no containers, no CI/CD

### Tenancy Mechanism
The application supports 3 demo tenants (`acme_corp`, `globex_inc`, `initech`) via a shared-everything model:

- **Backend**: `TenantMiddleware` (`app/middleware.py`) reads `X-Tenant-ID` HTTP header, falls back to `CURRENT_TENANT` global in `app/config.py`. The `set_current_tenant()` function (config.py:121-126) mutates the global `CURRENT_TENANT` at runtime. `KNOWN_TENANTS` list (config.py:23) is appended to when new tenants are encountered.
- **Frontend**: `TenantContext.tsx` provides React context with mutable tenant state. `fetchWithTenant.ts` wraps `fetch()` to inject `X-Tenant-ID` header. `socket.ts` has `reconnectSocket()` that disconnects and reconnects Socket.io on tenant change. All 4 data hooks (`GetAccounts`, `GetTrades`, `GetPositions`, `GetPeople`) depend on `[tenant]` in their `useEffect` dependencies, refetching data when tenant changes. `App.tsx` renders a `TenantSelector` dropdown.

### Database Layout
Single SQLite database with all tenants sharing the same tables, separated only by a `tenant_id` column:

| Table | Primary Key | Tenant Isolation |
|---|---|---|
| `accounts` | `id` (auto-increment) | `tenant_id` column |
| `account_users` | composite (`account_id`, `tenant_id`, `username`) | `tenant_id` column |
| `trades` | `id` (auto-increment) | `tenant_id` column |
| `positions` | composite (`account_id`, `tenant_id`, `security`) | `tenant_id` column |

### Inter-Module Coupling
- **God service**: `trade_processor.py` (1,047 lines) handles trade validation, processing, state machine, position management, Socket.io publishing, reporting, audit, and tenant-specific rules
- **Cross-domain queries**: `trade_processor.py` directly queries `Account` and `AccountUser` tables for trade validation (`validate_account_exists()`, `validate_account_has_users()`)
- **Circular dependency**: `account_service.py` lazily imports `count_trades_for_account` from `trade_processor.py`
- **Inconsistent service layer**: Some route handlers use services (`account_service`, `trade_processor`), others issue raw inline SQLAlchemy queries (e.g., `GET /trades/`, `GET /positions/*`)
- **Global mutable state**: `_runtime_state` dict in `config.py` mutated from `trade_processor.py`; tenant business rules (`TENANT_MAX_ACCOUNTS`, `TENANT_ALLOWED_SIDES`, `TENANT_AUTO_SETTLE`) stored as shared dicts in `config.py`

### Deployment Model
- Manual: `deploy.sh` installs deps, seeds DB, starts backend + frontend
- No Dockerfiles, no docker-compose, no CI/CD pipeline
- No health check verification in deployment

---

## Target State

### Single-Tenant Isolated Deployables
Each running instance serves exactly **one tenant**, configured at startup via `TENANT_ID` environment variable:

- Application crashes immediately if `TENANT_ID` is not set
- Requests with a mismatched `X-Tenant-ID` header are rejected with 403
- No mutable tenant state at runtime — tenant is immutable for the lifetime of the process
- Frontend reads `REACT_APP_TENANT_ID` at build time (baked into the bundle)

### Database-per-Tenant
- Each tenant gets its own SQLite database file (e.g., `app_acme_corp.db`)
- `DATABASE_URL` environment variable overrides for production (tenant-specific managed database)
- Cross-tenant queries are impossible by design

### Extracted Services
Two independent services aligned with domain boundaries:

| Service | Port | Domain | Responsibilities |
|---|---|---|---|
| **users-service** | 8001 | Accounts + People | Account CRUD, account-user management, people directory |
| **trades-service** | 8002 | Trading + Positions + Reference Data | Trade submission/processing, position tracking, reference data (S&P 500), Socket.io real-time |

Each service:
- Requires `TENANT_ID` at startup (fail-fast)
- Has its own database (no shared DB access)
- Exposes `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- Has an OpenAPI spec accessible at `/docs`
- Emits structured JSON logs with `tenant_id` and `service` fields
- Handles `SIGTERM` gracefully
- Communicates with other services via HTTP APIs only

### Frontend URL Mapping
| API Path | Service | Local URL |
|---|---|---|
| `/account/*`, `/accountuser/*`, `/people/*` | users-service | `http://localhost:8001` |
| `/trade/*`, `/trades/*`, `/positions/*`, `/stocks/*` | trades-service | `http://localhost:8002` |
| Socket.io (trade feed) | trades-service | `http://localhost:8002` |

### Infrastructure (Process B)
- Dockerized: Each service has its own `Dockerfile`
- Kubernetes: Deployed to EKS/AKS with Deployments, Services, HPA
- CI/CD: GitHub Actions with lint, test, build, deploy pipeline
- IaC: Terraform for all infrastructure

---

## Phased Approach

### Process A (This Migration)
1. **Migration Documentation** — This document + Definition of Done checklist
2. **Single-Tenant Runtime** — Remove multi-tenant switching, require `TENANT_ID` at startup, enforce in middleware, strip frontend tenant UI
3. **Data Isolation** — Database-per-tenant via `TENANT_ID` in connection string
4. **Service Extraction** — Extract `users-service` and `trades-service` under `services/`, break cross-domain coupling, add health endpoints, OpenAPI specs, structured logging

### Process B (Next Step)
5. **Containerization** — Dockerfiles for each service
6. **CI/CD** — GitHub Actions pipeline
7. **Infrastructure as Code** — Terraform for cloud infrastructure
8. **Smoke Testing** — End-to-end validation in deployed environment
