# TraderX Migration Plan — Multi-Tenant to Single-Tenant

## Current State

### Tech Stack

- **Backend**: Python 3.11+ / FastAPI monolith running on uvicorn (ASGI), port 8000
- **Frontend**: React (Create React App) on port 3000
- **Database**: SQLite via SQLAlchemy ORM — single file `traderx.db`
- **Real-time**: Socket.io server embedded in the same ASGI process
- **Deployment**: Manual `deploy.sh` script — no containers, no CI/CD, no IaC

### Tenancy Mechanism

The application supports 3 demo tenants (`acme_corp`, `globex_inc`, `initech`) via a header-based multi-tenant model:

1. **Request path**: The `X-Tenant-ID` HTTP header is read by `TenantMiddleware` (`app/middleware.py`) and stored on `request.state.tenant_id`. If the header is absent, the middleware falls back to the `CURRENT_TENANT` global variable (default: `acme_corp`).

2. **Mutable global state** (`app/config.py`):
   - `CURRENT_TENANT` — mutable global variable modified at runtime via `set_current_tenant()`
   - `KNOWN_TENANTS` — list appended to at runtime when new tenants are encountered
   - `_runtime_state` — dict mutated from multiple modules (trade counts, timestamps, session counts)
   - `set_current_tenant()` — function that mutates the global and appends to `KNOWN_TENANTS`

3. **Frontend tenant switching** (`web-front-end/react/src/`):
   - `TenantContext.tsx` — React context holding mutable `tenant` state with `TenantProvider`
   - `fetchWithTenant.ts` — HTTP wrapper that injects `X-Tenant-ID` header on every request
   - `App.tsx` — `TenantSelector` dropdown component that calls `setCurrentTenant()`, `reconnectSocket()`, and `setTenant()` on change
   - `socket.ts` — `reconnectSocket()` disconnects and recreates the Socket.io connection with a new tenant query param
   - All data hooks (`GetAccounts`, `GetTrades`, `GetPositions`, `GetPeople`) depend on `[tenant]` in their `useEffect` dependencies

### Database Layout

Single SQLite database file (`traderx.db`) with 4 tables. All tenants share the same tables, separated only by a `tenant_id` column:

| Table | Primary Key | Tenant Column |
|---|---|---|
| `accounts` | `id` (auto-increment) | `tenant_id` |
| `account_users` | composite (`account_id`, `tenant_id`, `username`) | `tenant_id` |
| `trades` | `id` (auto-increment) | `tenant_id` |
| `positions` | composite (`account_id`, `tenant_id`, `security`) | `tenant_id` |

Schema defined in SQLAlchemy models: `app/models/account.py`, `app/models/trade.py`, `app/models/position.py`. Database engine created in `app/database.py`. Seed data for all 3 tenants in `app/seed.py`.

### Inter-Module Coupling

1. **God service**: `app/services/trade_processor.py` (1,047 lines) handles trade validation, processing, state machine, position management, Socket.io publishing, reporting/aggregation, tenant-specific rules, batch processing, and audit logging. It directly queries `Account` and `AccountUser` tables (cross-domain).

2. **Circular dependency**: `trade_processor.py` imports `Account`/`AccountUser` models from `app/models/account.py`. `account_service.py` lazily imports `count_trades_for_account` from `trade_processor.py` to avoid import-time failure.

3. **Inconsistent service layer usage**:
   - `GET /trades/` uses raw inline SQLAlchemy query (bypasses `trade_processor.get_all_trades()`)
   - `GET /positions/*` endpoints use raw inline queries (bypasses trade_processor position functions)
   - `GET /account/{id}` directly queries the `positions` table for portfolio summary

4. **Shared config import**: Every module uses `from app.config import *`, pulling in all mutable globals.

### Non-HTTP Entry Points

None. No background workers, scheduled jobs, message queue consumers, or CLI commands.

### Shared Caches

- `_stocks_cache` in `app/utils/helpers.py` — S&P 500 data loaded from CSV
- `_people_cache` in `app/utils/helpers.py` — people data loaded from JSON
- `_people` in `app/services/people_service.py` — Person objects loaded from JSON

---

## Target State

### Single-Tenant Isolated Deployables

Each running instance serves exactly **one tenant**, configured at startup via the `TENANT_ID` environment variable. The application fails fast at startup if `TENANT_ID` is not set. Requests with a mismatched `X-Tenant-ID` header are rejected with HTTP 403.

### Database-per-Tenant

Each tenant gets its own isolated database. The default SQLite connection string incorporates `TENANT_ID` (e.g., `sqlite:///app_{TENANT_ID}.db`). In production, `DATABASE_URL` overrides this to point at a tenant-specific managed database (PostgreSQL/Azure SQL).

### Extracted Services

The monolith is decomposed into 5 independent services aligned with domain boundaries per `TARGET_ARCHITECTURE_CONSTRAINTS.md`:

| Service | Port | Domain | Responsibilities |
|---|---|---|---|
| **Account Service** | 8001 | Accounts | Account CRUD, account user management, account validation |
| **Trading Service** | 8002 | Trading | Trade submission, trade validation, trade state machine, Socket.io publishing |
| **Position Service** | 8003 | Positions | Position tracking, position queries, position recalculation |
| **Reference Data Service** | 8004 | Reference Data | Stock ticker lookup, S&P 500 data |
| **People Service** | 8005 | People | Person directory, person validation |

Each service:
- Requires `TENANT_ID` at startup (fail-fast)
- Has its own database (no shared DB access)
- Exposes `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- Has an OpenAPI spec (auto-generated by FastAPI)
- Emits structured JSON logs with `tenant_id` and `service` fields
- Handles SIGTERM gracefully
- Communicates with other services via HTTP APIs only

### Frontend

The React frontend reads `REACT_APP_TENANT_ID` at build time (baked into the bundle). No runtime tenant switching. API URLs point at the extracted service ports (ready for Process B to re-point at ALB).

### Infrastructure (Process B)

- Dockerized containers for all services
- Kubernetes deployment (EKS/AKS) with Terraform IaC
- GitHub Actions CI/CD pipeline
- API gateway for routing, auth, rate limiting

---

## Phased Approach

### Process A (this migration)

| Phase | Description | Deliverables |
|---|---|---|
| 1. Migration Documentation | Document current state, target state, phased plan | `migration/MIGRATION_PLAN.md`, `migration/DEFINITION_OF_DONE.md` |
| 2. Single-Tenant Runtime | Remove tenant-switching, require `TENANT_ID` env var, enforce in middleware, strip frontend tenant UI | Modified monolith + frontend running in single-tenant mode |
| 3. Data Isolation | Database-per-tenant via `TENANT_ID` in connection string | Tenant-specific database files |
| 4. Service Extraction | Decompose monolith into 5 domain services with HTTP inter-service communication | `services/` directory with 5 independent services |

### Process B (next step — not in scope)

| Phase | Description |
|---|---|
| 5. Containerization | Dockerfiles for all services |
| 6. CI/CD | GitHub Actions pipelines |
| 7. Infrastructure as Code | Terraform for EKS/AKS, RDS, ECR, ALB |
| 8. Smoke Testing | End-to-end smoke tests against deployed services |

---

## Frontend URL Mapping

After service extraction, the React frontend API calls are routed as follows:

| API Path | Target Service | URL |
|---|---|---|
| `/account/*`, `/accountuser/*` | Account Service | `http://localhost:8001` |
| `/trade/`, `/trades/*` | Trading Service | `http://localhost:8002` |
| `/positions/*` | Position Service | `http://localhost:8003` |
| `/stocks/*` | Reference Data Service | `http://localhost:8004` |
| `/people/*` | People Service | `http://localhost:8005` |

In Process B, these will be re-pointed at the ALB/API Gateway URL.
