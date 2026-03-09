# TraderX Migration Guide: Multi-Tenant to Single-Tenant

This document describes the migration of TraderX from a shared multi-tenant monolith to a single-tenant, cloud-native architecture suitable for isolated per-tenant deployments.

---

## 1. Migration Overview

### Before (Legacy Architecture)
- **Single Python/FastAPI monolith** serving all tenants in one process
- **Shared SQLite database** with `tenant_id` column for row-level separation
- **Global mutable config** (`config.py`) with `CURRENT_TENANT`, `KNOWN_TENANTS`, `_runtime_state`
- **God service** (`trade_processor.py`, 1047 lines) handling all business logic
- **Circular dependencies** between `account_service.py` and `trade_processor.py`
- **Cross-domain database queries** (trade processor directly queries account tables)
- **No containerization**, no CI/CD, manual `deploy.sh` deployment
- **Multi-tenant frontend** with tenant selector dropdown and `X-Tenant-ID` header injection

### After (Target Architecture)
- **Single-tenant deployment model**: each tenant gets its own isolated set of services
- **Database-per-tenant**: no `tenant_id` columns; isolation enforced at infrastructure level
- **Clean service boundaries**: decomposed god service into focused modules
  - `trading_service.py` — trade validation, processing, state machine
  - `position_service.py` — position CRUD, queries, recalculation
  - `reporting_service.py` — analytics, aggregation, audit queries
- **No circular dependencies**: clean dependency graph (DAG)
- **Environment-injected configuration**: all per-tenant config via env vars
- **Containerized services**: Docker images for backend and frontend
- **Kubernetes-deployable**: Deployments, Services, HPAs, Ingress
- **CI/CD pipelines**: GitHub Actions for build, test, deploy
- **Terraform IaC**: AWS EKS, RDS, ECR provisioning

---

## 2. Code Changes Summary

### Configuration (`app/config.py`)
| Removed | Rationale |
|---|---|
| `CURRENT_TENANT`, `DEFAULT_TENANT` | No tenant multiplexing in single-tenant mode |
| `KNOWN_TENANTS` list | Each deployment is one tenant |
| `set_current_tenant()` | No runtime tenant switching |
| `TENANT_MAX_ACCOUNTS` dict | Replaced by `MAX_ACCOUNTS` env var |
| `TENANT_ALLOWED_SIDES` dict | Replaced by `ALLOWED_SIDES` env var |
| `TENANT_AUTO_SETTLE` dict | Replaced by `AUTO_SETTLE` env var |
| `_runtime_state` mutable dict | Replaced by proper per-request state |
| `from app.config import *` pattern | Replaced with explicit imports |

### Middleware (`app/middleware.py`)
- `TenantMiddleware` removed entirely — no `X-Tenant-ID` header processing needed

### Models
- `tenant_id` column removed from `Account`, `AccountUser`, `Trade`, `Position`
- Composite primary keys simplified (no `tenant_id` component)
- `to_dict()` methods no longer include `tenant_id`

### Services
- **`trade_processor.py` decomposed** into:
  - `trading_service.py` — trade validation, `process_trade()`, state machine
  - `position_service.py` — position CRUD, recalculation
  - `reporting_service.py` — portfolio summary, analytics, audit
- **Circular dependency eliminated**: `account_service.py` no longer imports from trade_processor
- **Cross-domain queries removed**: services use API-style function calls instead of direct DB access to other domains

### Routes
- All `tenant_id` parameters removed from route handlers
- All `get_tenant_from_request()` calls removed
- Inline SQLAlchemy queries replaced with service layer calls (consistency fix)

### Frontend (React)
- `TenantContext.tsx` removed
- `TenantProvider` wrapper removed from `App.tsx`
- `TenantSelector` component removed
- `fetchWithTenant.ts` replaced with standard `fetch()`
- `socket.ts` simplified (no tenant-based reconnection)

### Database Seeding (`app/seed.py`)
- Seeds data for a single deployment (no multi-tenant distribution)
- Sample accounts, trades, and positions without `tenant_id`

---

## 3. Environment Variables

The following environment variables configure a single-tenant deployment:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///traderx.db` | Database connection string (use PostgreSQL in production) |
| `APP_PORT` | `8000` | Backend server port |
| `APP_HOST` | `0.0.0.0` | Backend bind address |
| `MAX_ACCOUNTS` | `100` | Maximum accounts for this tenant |
| `ALLOWED_SIDES` | `Buy,Sell` | Comma-separated allowed trade sides |
| `AUTO_SETTLE` | `true` | Whether trades auto-settle |
| `MAX_TRADE_QUANTITY` | `1000000` | Maximum trade quantity |
| `MIN_TRADE_QUANTITY` | `1` | Minimum trade quantity |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 4. Deployment Model

Each tenant is deployed as an independent stack:

```
Tenant A                          Tenant B
┌─────────────────────┐          ┌─────────────────────┐
│  Frontend (React)   │          │  Frontend (React)   │
│  Backend (FastAPI)  │          │  Backend (FastAPI)  │
│  Database (PG)      │          │  Database (PG)      │
└─────────────────────┘          └─────────────────────┘
        │                                │
        └────── Kubernetes Cluster ──────┘
                (namespace isolation)
```

- **Namespace isolation**: `traderx-<tenant>-<env>` (e.g., `traderx-acme-prod`)
- **Database isolation**: Separate RDS instance or schema per tenant
- **Network isolation**: Kubernetes NetworkPolicies prevent cross-tenant traffic
- **Secret isolation**: Per-tenant Kubernetes Secrets for DB credentials

---

## 5. Running Locally

```bash
# Backend
cd traderx-monolith
pip install -r requirements.txt
python run.py

# Frontend
cd web-front-end/react
npm install
npm start
```

Backend: http://localhost:8000
Frontend: http://localhost:3000
