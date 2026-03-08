# TraderX Monolith Migration Plan

## Current State

### Tech Stack
- **Language/Framework**: Python 3.12 / FastAPI
- **Database**: SQLite (single file `traderx.db`)
- **ORM**: SQLAlchemy with declarative base
- **Real-time**: python-socketio (ASGI mode) for trade/position updates
- **Entry point**: `run.py` starts uvicorn serving `app.main:combined_app` (FastAPI + Socket.io ASGI composite)

### Tenancy Mechanism
The application uses a **mutable global tenant model**:

- `app/config.py` defines `CURRENT_TENANT` as a mutable global variable, defaulting to `"acme_corp"`
- `set_current_tenant(tenant_id)` mutates the global `CURRENT_TENANT` and appends unknown tenants to `KNOWN_TENANTS` list
- `app/middleware.py` (`TenantMiddleware`) reads `X-Tenant-ID` HTTP header and falls back to `CURRENT_TENANT` global
- Tenant ID is stored on `request.state.tenant_id` and extracted in route handlers via `get_tenant_from_request()` in `app/utils/helpers.py`
- Tenant-specific business rules are stored in shared dicts in `config.py`: `TENANT_MAX_ACCOUNTS`, `TENANT_ALLOWED_SIDES`, `TENANT_AUTO_SETTLE`

### Database Layout
- Single SQLite database file (`traderx.db`) shared across all tenants
- All tables have a `tenant_id` column for row-level filtering:
  - `accounts` (id, tenant_id, display_name)
  - `account_users` (account_id, tenant_id, username) — composite PK
  - `trades` (id, tenant_id, account_id, security, side, quantity, state, created, updated)
  - `positions` (account_id, tenant_id, security, quantity, updated) — composite PK
- `app/database.py` creates a single `engine` and `SessionLocal` from `DATABASE_URL` config
- `app/seed.py` seeds data for 3 tenants: `acme_corp`, `globex_inc`, `initech`

### Inter-Module Coupling
- **Circular dependency**: `app/services/account_service.py` imports `count_trades_for_account` from `app/services/trade_processor.py` (via lazy import), while `trade_processor.py` imports `Account` and `AccountUser` models from `app/models/account.py`
- **Cross-domain queries in trade_processor.py**: `validate_account_exists()` and `validate_account_has_users()` directly query the `accounts` and `account_users` tables
- **Cross-domain queries in routes/accounts.py**: `get_account()` endpoint directly queries the `positions` table for portfolio summary
- **God module**: `app/services/trade_processor.py` (1047 lines) handles trade validation, processing, position management, Socket.io publishing, reporting, tenant-specific rules, and cross-domain queries
- **Reference data**: `app/utils/helpers.py` loads S&P 500 CSV and people JSON data, cached in module-level globals (`_stocks_cache`, `_people_cache`)

### Shared Mutable State
- `CURRENT_TENANT` global in `config.py` — mutated by `set_current_tenant()`
- `KNOWN_TENANTS` list in `config.py` — appended to at runtime
- `_runtime_state` dict in `config.py` — mutated from `trade_processor.py` via `update_runtime_state()`
- `_sio` module-level variable in `trade_processor.py` — set once at startup
- `_stocks_cache` in `helpers.py` — lazy-loaded, cached
- `_people_cache` in `helpers.py` — lazy-loaded, cached
- `_people` in `people_service.py` — lazy-loaded, cached

### Non-HTTP Entry Points
- Socket.io server events: `connect`, `disconnect`, `subscribe`, `unsubscribe` (defined in `app/main.py`)
- Socket.io publishing: `publish_trade_update()`, `publish_position_update()` in `trade_processor.py`

### Deployment Model
- Manual: `python run.py` starts the monolith on port 8000
- No containerization, no CI/CD, no infrastructure as code

---

## Target State

### Single-Tenant Isolated Deployables
- Each running instance serves **exactly one tenant**, configured at startup via `TENANT_ID` environment variable
- Application **fails fast** at startup if `TENANT_ID` is not set
- Requests with a mismatched `X-Tenant-ID` header are **rejected with 403**
- No shared mutable tenant state — `CURRENT_TENANT`, `KNOWN_TENANTS`, `set_current_tenant()` are removed

### Database-per-Tenant
- Each tenant gets its own SQLite database file (e.g., `app_acme_corp.db`)
- `DATABASE_URL` environment variable overrides for production (points to tenant-specific managed database)
- `tenant_id` column is no longer needed for row-level filtering; isolation is enforced at the infrastructure level

### Extracted Services
Two domain services aligned with the user-specified boundaries:

| Service | Port | Domain | Routes |
|---------|------|--------|--------|
| **users** | 8001 | Account management, account-user management, people directory | `/account/*`, `/accountuser/*`, `/people/*` |
| **trades** | 8002 | Trade submission, trade processing, position tracking, real-time updates | `/trade/*`, `/trades/*`, `/positions/*`, `/stocks/*`, Socket.io |

Each service:
- Requires `TENANT_ID` at startup (fail-fast)
- Has its own database
- Exposes `/health` endpoint returning `{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`
- Emits structured JSON logs with `tenant_id` and `service` fields
- Has an OpenAPI spec accessible at `/docs`
- Handles SIGTERM gracefully
- Communicates with other services via HTTP APIs only (no shared DB access)

### Cross-Service Communication
- **trades -> users**: HTTP call to validate account exists (replaces direct Account table query)
- **users -> trades**: No direct dependency (accounts route no longer queries positions table directly)
- Inter-service URLs configured via environment variables: `USERS_SERVICE_URL`, `TRADES_SERVICE_URL`

### Infrastructure (Process B)
- Dockerized services with minimal base images
- Kubernetes deployment (EKS/AKS) with Helm charts
- GitHub Actions CI/CD pipeline
- Terraform for infrastructure as code

---

## Phased Approach

### Phase 1: Migration Documentation (Process A)
Create migration plan and definition of done documents.

### Phase 2: Single-Tenant Runtime (Process A)
- Remove `set_current_tenant()`, `KNOWN_TENANTS` runtime mutation, `_runtime_state`
- Require `TENANT_ID` environment variable at startup
- Update middleware to enforce single-tenant mode (reject mismatched headers with 403)
- Update tests to set `TENANT_ID` in environment

### Phase 3: Data Isolation (Process A)
- Update database connection string to incorporate `TENANT_ID`
- Each tenant gets its own database file
- Verify test isolation with in-memory database

### Phase 4: Service Extraction (Process A)
- Extract `users` service under `services/users/`
- Extract `trades` service under `services/trades/`
- Break circular dependency between account_service and trade_processor
- Replace cross-domain DB queries with HTTP API calls
- Add `/health` endpoints, OpenAPI specs, structured JSON logging, SIGTERM handling
- Add test suites for each service

### Phase 5: Containerization (Process B)
- Create Dockerfiles for each service
- Build and tag images

### Phase 6: CI/CD (Process B)
- Set up GitHub Actions pipelines
- Lint, test, build, deploy automation

### Phase 7: Infrastructure as Code (Process B)
- Terraform modules for cloud infrastructure
- Database-per-tenant provisioning
- Kubernetes cluster and manifests

### Phase 8: Smoke Testing (Process B)
- End-to-end smoke tests against deployed services
- Verify cross-service communication in staging
