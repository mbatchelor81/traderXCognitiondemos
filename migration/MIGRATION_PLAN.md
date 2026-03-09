# TraderX Migration Plan — Multi-Tenant to Single-Tenant

## Current State

### Tech Stack
- **Backend**: Python 3.11+ / FastAPI monolith running on uvicorn (ASGI), port 8000
- **Frontend**: React (Create React App) on port 3000
- **Database**: SQLite via SQLAlchemy ORM (`traderx.db`)
- **Real-time**: Socket.io server embedded in the ASGI process (python-socketio)
- **Entry point**: `traderx-monolith/run.py` → `app.main:combined_app`

### Tenancy Mechanism
The application supports multiple tenants via the `X-Tenant-ID` HTTP header:
- **`app/middleware.py`** — `TenantMiddleware` reads `X-Tenant-ID` from the request header, falls back to the `CURRENT_TENANT` global variable
- **`app/config.py`** — `CURRENT_TENANT` is a mutable global modified at runtime by `set_current_tenant()`. `KNOWN_TENANTS` list is appended to when new tenants are encountered
- **`app/config.py`** — `_runtime_state` dict is mutated from multiple modules (trade counts, timestamps, session counts)
- **Frontend** — `TenantContext.tsx` provides React context for mutable tenant state; `fetchWithTenant.ts` injects `X-Tenant-ID` header on every request; `socket.ts` reconnects WebSocket on tenant change; `App.tsx` renders a `TenantSelector` dropdown
- **3 demo tenants** pre-seeded: `acme_corp`, `globex_inc`, `initech`

### Database Layout
Single SQLite file (`traderx.db`) with all tenants sharing the same tables:

| Table | Primary Key | Tenant Column |
|---|---|---|
| `accounts` | `id` (auto-increment) | `tenant_id` |
| `account_users` | composite (`account_id`, `tenant_id`, `username`) | `tenant_id` |
| `trades` | `id` (auto-increment) | `tenant_id` |
| `positions` | composite (`account_id`, `tenant_id`, `security`) | `tenant_id` |

No row-level security, no schema isolation. Connection string: `sqlite:///traderx.db`.

### Inter-Module Coupling
- **God service**: `app/services/trade_processor.py` (1,047 lines) handles trade validation, processing, state machine, position management, Socket.io publishing, reporting, audit, and tenant-specific rules
- **Circular dependency**: `trade_processor.py` imports `Account`/`AccountUser` models; `account_service.py` lazily imports `count_trades_for_account` from `trade_processor`
- **Cross-domain queries**: `trade_processor.validate_account_exists()` directly queries the accounts table; `GET /account/{id}` directly queries the positions table; `GET /trades/` and `GET /positions/*` use inline SQLAlchemy queries bypassing the service layer
- **Shared helpers**: `app/utils/helpers.py` provides reference data loading, people data loading, validation, tenant helpers, and audit logging — imported everywhere via `from app.config import *`

### Non-HTTP Entry Points
- **Socket.io server**: Embedded in the ASGI process (`app/main.py`), handles `connect`, `disconnect`, `subscribe`, `unsubscribe` events. Trade and position updates are published to per-account rooms
- **Database seeding**: `app/seed.py` runs on first startup, seeds all 3 tenants into the shared database

### Deployment Model
- Manual deployment via `deploy.sh` — no containers, no CI/CD, no health checks
- Single process serves all tenants on port 8000
- Frontend served separately on port 3000

---

## Target State

### Single-Tenant Isolation
Each running instance serves exactly **one tenant**, configured at startup via `TENANT_ID` environment variable:
- Application crashes immediately if `TENANT_ID` is not set
- No mutable global tenant state — tenant is immutable for the lifetime of the process
- Requests with a mismatched `X-Tenant-ID` header are rejected with HTTP 403
- Frontend reads tenant from build-time `REACT_APP_TENANT_ID` environment variable (baked into bundle)

### Database-per-Tenant
Each tenant gets its own isolated database:
- Default: `sqlite:///app_{TENANT_ID}.db`
- Overridable via `DATABASE_URL` environment variable for production (pointing to a managed database per tenant)
- No `tenant_id` column needed for row-level filtering — isolation is at the infrastructure level

### Extracted Services
The monolith is decomposed into 5 independent services per `TARGET_ARCHITECTURE_CONSTRAINTS.md`:

| Service | Port | Domain | Responsibilities |
|---|---|---|---|
| **Account Service** | 8001 | Accounts | Account CRUD, account user management, account validation |
| **Trading Service** | 8002 | Trading | Trade submission, validation, state machine, Socket.io publishing |
| **Position Service** | 8003 | Positions | Position tracking, queries, recalculation |
| **Reference Data Service** | 8004 | Reference Data | S&P 500 stock ticker lookup |
| **People Service** | 8005 | People | Person directory, validation |

Each service:
- Requires `TENANT_ID` at startup (fail-fast)
- Has its own database (database-per-tenant)
- Exposes a `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- Has an OpenAPI spec accessible at `/docs`
- Emits structured JSON logs with `tenant_id` and `service` fields
- Handles SIGTERM gracefully
- Communicates with other services via HTTP APIs only (no shared DB access)

### Frontend
- API URLs point at individual extracted service ports (ready for Process B to re-point at ALB)
- No mutable tenant state — `REACT_APP_TENANT_ID` is a build-time constant
- No tenant selector dropdown, no `fetchWithTenant`, no socket reconnect on tenant change

### Infrastructure (Process B)
- Dockerized services with minimal base images
- Kubernetes deployable (EKS/AKS)
- GitHub Actions CI/CD pipeline
- Terraform for infrastructure as code

---

## Phased Approach

### Process A (This Migration)

| Phase | Description | Status |
|---|---|---|
| 1. Migration Documentation | Create migration plan and definition of done | In Progress |
| 2. Single-Tenant Runtime | Remove multi-tenant logic, require `TENANT_ID` at startup | Planned |
| 3. Data Isolation | Database-per-tenant using `TENANT_ID` in connection strings | Planned |
| 4. Service Extraction | Decompose monolith into 5 services under `services/` | Planned |

### Process B (Future — Containerization, CI/CD, IaC)

| Phase | Description | Status |
|---|---|---|
| 5. Containerization | Dockerfiles for all services | Planned |
| 6. CI/CD | GitHub Actions pipeline for lint, test, build, deploy | Planned |
| 7. Infrastructure as Code | Terraform for VPC, EKS/AKS, RDS, ECR/ACR, ALB | Planned |
| 8. Smoke Testing | End-to-end tests against deployed infrastructure | Planned |

---

## Frontend URL Mapping

After service extraction, the frontend will point at individual service URLs:

| API Path | Current Target | Extracted Service Target |
|---|---|---|
| `/account/*`, `/accountuser/*` | `http://localhost:8000` | `http://localhost:8001` (Account Service) |
| `/trade/`, `/trades/*` | `http://localhost:8000` | `http://localhost:8002` (Trading Service) |
| `/positions/*` | `http://localhost:8000` | `http://localhost:8003` (Position Service) |
| `/stocks/*` | `http://localhost:8000` | `http://localhost:8004` (Reference Data Service) |
| `/people/*` | `http://localhost:8000` | `http://localhost:8005` (People Service) |
| Socket.io (trade feed) | `http://localhost:8000` | `http://localhost:8002` (Trading Service) |
