# TraderX — Legacy Trading Platform

[![CI](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml/badge.svg)](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml)

A multi-tenant financial trading platform built as a Python/FastAPI monolith with a React frontend. TraderX supports account management, trade execution, position tracking, and real-time updates via Socket.io. It uses SQLite for storage and ships with three demo tenants (`acme_corp`, `globex_inc`, `initech`).

> **Note:** This is a legacy monolith with intentional technical debt, designed as a reference application for exploring modernization and microservice decomposition strategies.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Multi-Tenancy](#multi-tenancy)
- [Real-Time Updates](#real-time-updates)
- [Testing](#testing)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Prerequisites

| Tool       | Version | Purpose           |
|------------|---------|-------------------|
| Python     | 3.11+   | Backend (FastAPI) |
| Node.js    | 18+     | Frontend (React)  |
| npm        | 9+      | Package manager   |

---

## Quick Start

### 1. Start the backend

```bash
cd traderx-monolith
pip install -r requirements.txt
python run.py
```

On first run the backend will:
1. Create the SQLite database (`traderx.db`)
2. Seed it with sample accounts, trades, and positions across all three tenants
3. Start the FastAPI server at **http://localhost:8000**

Interactive API docs are available at **http://localhost:8000/docs** (Swagger UI).

### 2. Start the frontend

```bash
cd web-front-end/react
npm install
npm start
```

The React UI will be available at **http://localhost:3000**.

### 3. Open the app

Navigate to [http://localhost:3000](http://localhost:3000) in your browser. Select a tenant from the dropdown in the top-right corner, choose an account, and start trading.

---

## Project Structure

```
traderXCognitiondemos/
├── traderx-monolith/              # Python/FastAPI backend
│   ├── run.py                     # Application entry point
│   ├── requirements.txt           # Python dependencies
│   ├── data/
│   │   ├── s-and-p-500-companies.csv  # S&P 500 reference data
│   │   └── people.json            # User directory (20 people)
│   ├── app/
│   │   ├── main.py                # FastAPI app + Socket.io mount
│   │   ├── config.py              # Global configuration (mutable state)
│   │   ├── database.py            # SQLAlchemy engine & session
│   │   ├── seed.py                # Demo data seeder
│   │   ├── middleware.py          # Tenant injection middleware
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── account.py         # Account, AccountUser
│   │   │   ├── trade.py           # Trade
│   │   │   └── position.py        # Position
│   │   ├── routes/                # FastAPI route handlers
│   │   │   ├── accounts.py        # /account/, /accountuser/
│   │   │   ├── trades.py          # /trade/, /trades/
│   │   │   ├── positions.py       # /positions/
│   │   │   ├── people.py          # /people/
│   │   │   └── reference_data.py  # /stocks/
│   │   ├── services/
│   │   │   ├── trade_processor.py # Core trade engine (~1000 lines)
│   │   │   ├── account_service.py # Account business logic
│   │   │   └── people_service.py  # People directory service
│   │   └── utils/
│   │       └── helpers.py         # Shared utilities
│   └── tests/
│       ├── conftest.py            # Pytest fixtures (in-memory SQLite)
│       ├── test_account_crud.py   # Account endpoint tests
│       └── test_trade_submit.py   # Trade submission tests
├── web-front-end/react/           # React SPA frontend
│   ├── src/
│   │   ├── App.tsx                # Root component with tenant selector
│   │   ├── Datatable/             # AG Grid blotters (trades & positions)
│   │   ├── ActionButtons/         # Create Account, Trade, AccountUser dialogs
│   │   ├── AccountsDropdown/      # Account selector
│   │   ├── hooks/                 # Data fetching hooks
│   │   ├── TenantContext.tsx      # React context for tenant state
│   │   ├── fetchWithTenant.ts     # Fetch wrapper with X-Tenant-ID header
│   │   └── socket.ts             # Socket.io client connection
│   └── package.json
├── docs/                          # Original FINOS TraderX documentation
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── .windsurf/skills/              # AI agent skills for development
├── .agents/skills/                # Additional agent skills
├── LEGACY_ARCHITECTURE.md         # Current architecture & known tech debt
├── TARGET_ARCHITECTURE_CONSTRAINTS.md  # Future microservices target state
├── CONTRIBUTING.md                # FINOS contribution guidelines
├── deploy.sh                      # Manual deployment script
└── LICENSE                        # Apache 2.0
```

---

## Architecture

TraderX is a **monolith-first** application. The backend is a single FastAPI process that handles all business logic, with a React SPA connecting over REST and WebSocket:

```
┌──────────────────────────────────────────────────┐
│              Browser (React UI :3000)             │
└─────────┬────────────────────────────┬───────────┘
          │ REST API                   │ WebSocket
          ▼                            ▼
┌──────────────────────────────────────────────────┐
│            FastAPI Monolith (:8000)               │
│                                                   │
│  Routes: /account, /trade, /trades, /positions,   │
│          /stocks, /people, /health                │
│                                                   │
│  Services: trade_processor (god service),         │
│            account_service, people_service         │
│                                                   │
│  Socket.io: embedded async server for real-time   │
│             trade & position push updates          │
│                                                   │
│  Database: SQLAlchemy ORM → SQLite (traderx.db)   │
│  Tables: accounts, account_users, trades,         │
│          positions (all tenant-isolated by column) │
└──────────────────────────────────────────────────┘
```

### Known Technical Debt

This is a **legacy application by design** with intentional architectural smells:

- **God service** — `trade_processor.py` (~1000 lines) owns trade validation, processing, position updates, Socket.io publishing, and cross-domain queries
- **Mutable global state** — `config.py` is imported via `from app.config import *` across every module
- **Circular dependencies** — `trade_processor` and `account_service` import each other
- **Shared multi-tenant database** — all tenants share the same SQLite tables, isolated only by a `tenant_id` column

For a full breakdown see [LEGACY_ARCHITECTURE.md](LEGACY_ARCHITECTURE.md). For the target microservices architecture see [TARGET_ARCHITECTURE_CONSTRAINTS.md](TARGET_ARCHITECTURE_CONSTRAINTS.md).

---

## API Reference

All endpoints accept an optional `X-Tenant-ID` header. If omitted, the default tenant (`acme_corp`) is used.

### Accounts

| Method | Endpoint               | Description                            |
|--------|------------------------|----------------------------------------|
| `GET`  | `/account/`            | List all accounts for the current tenant |
| `POST` | `/account/`            | Create a new account                   |
| `PUT`  | `/account/`            | Update an existing account             |
| `GET`  | `/account/{account_id}`| Get account by ID with portfolio summary |

### Account Users

| Method | Endpoint          | Description               |
|--------|-------------------|---------------------------|
| `GET`  | `/accountuser/`   | List all account users    |
| `POST` | `/accountuser/`   | Create a new account user |
| `PUT`  | `/accountuser/`   | Update an account user    |

### Trading

| Method | Endpoint               | Description                         |
|--------|------------------------|-------------------------------------|
| `POST` | `/trade/`              | Submit a new trade order            |
| `GET`  | `/trades/`             | List all trades for the current tenant |
| `GET`  | `/trades/{account_id}` | List trades for a specific account  |

### Positions

| Method | Endpoint                   | Description                              |
|--------|----------------------------|------------------------------------------|
| `GET`  | `/positions/`              | List all positions for the current tenant |
| `GET`  | `/positions/{account_id}`  | List positions for a specific account    |

### Reference Data

| Method | Endpoint          | Description                |
|--------|-------------------|----------------------------|
| `GET`  | `/stocks/`        | List all S&P 500 stocks    |
| `GET`  | `/stocks/{ticker}`| Get stock by ticker symbol |

### People Directory

| Method | Endpoint                   | Description                              |
|--------|----------------------------|------------------------------------------|
| `GET`  | `/people/GetPerson`        | Get a person by LogonId or EmployeeId    |
| `GET`  | `/people/GetMatchingPeople`| Search for people matching text          |
| `GET`  | `/people/ValidatePerson`   | Validate that a person exists            |

### System

| Method | Endpoint        | Description                           |
|--------|-----------------|---------------------------------------|
| `GET`  | `/`             | Service info (name, version, status)  |
| `GET`  | `/health`       | Health check                          |
| `GET`  | `/sentry-debug` | Trigger a test error for Sentry       |

---

## Multi-Tenancy

TraderX supports multiple tenants via the `X-Tenant-ID` HTTP header. The frontend includes a tenant selector in the top navigation bar that switches the active tenant context.

### Available Tenants

| Tenant ID    | Accounts | Trades | Positions | Description                    |
|-------------|----------|--------|-----------|--------------------------------|
| `acme_corp`  | 2        | 8      | 7         | Default tenant                 |
| `globex_inc` | 2        | 5      | 5         | Secondary demo tenant          |
| `initech`    | 3        | 8      | 7         | Third tenant (auto-settle off) |

### Example

```bash
# List accounts for the default tenant (acme_corp)
curl http://localhost:8000/account/

# List accounts for a specific tenant
curl -H "X-Tenant-ID: globex_inc" http://localhost:8000/account/
```

---

## Real-Time Updates

The backend embeds a Socket.io server (mounted on the same ASGI process at port `8000`). When a trade is submitted, the trade processor publishes updates to Socket.io rooms so connected frontends receive live trade and position data without polling.

The React frontend connects automatically and subscribes to rooms based on the selected account (e.g., `/accounts/{id}/trades`). A connection status indicator in the app bar shows whether the WebSocket link is active.

---

## Testing

### Backend tests

```bash
cd traderx-monolith
python -m pytest tests/ -v
```

Tests use an **in-memory SQLite** database (configured in `conftest.py`) so they run fast and don't touch the development database.

### Frontend lint & build

```bash
cd web-front-end/react
npm run lint          # ESLint (TypeScript)
npm run build         # Production build
```

### CI

A [GitHub Actions workflow](.github/workflows/ci.yml) runs on every pull request:
- **Backend Tests** — Python 3.12, `pytest`
- **Frontend Checks** — Node 20, `npm run lint`, `npm run build`

---

## Configuration

All backend configuration is managed via environment variables with sensible defaults in [`config.py`](traderx-monolith/app/config.py).

| Variable                    | Default             | Description                          |
|-----------------------------|---------------------|--------------------------------------|
| `DATABASE_URL`              | `sqlite:///traderx.db` | SQLAlchemy connection string      |
| `DEFAULT_TENANT`            | `acme_corp`         | Fallback tenant when no header set   |
| `APP_PORT`                  | `8000`              | Backend server port                  |
| `APP_HOST`                  | `0.0.0.0`           | Backend bind address                 |
| `DEBUG`                     | `true`              | Enable hot-reload and debug logging  |
| `LOG_LEVEL`                 | `INFO`              | Logging level                        |
| `SENTRY_DSN`                | *(empty)*           | Sentry DSN for error monitoring      |
| `TRADE_PROCESSING_DELAY_MS` | `0`                | Artificial processing delay (ms)     |
| `MAX_TRADE_QUANTITY`        | `1000000`           | Maximum allowed trade quantity       |
| `MIN_TRADE_QUANTITY`        | `1`                 | Minimum allowed trade quantity       |
| `CORS_ORIGINS`              | `*`                 | Comma-separated allowed origins      |
| `AUDIT_ENABLED`             | `true`              | Enable audit logging                 |

The React frontend port defaults to `3000` (or the value of `WEB_SERVICE_REACT_PORT`).

---

## Deployment

A basic deployment script is included:

```bash
./deploy.sh [environment]
```

This installs dependencies, seeds the database, starts the backend, builds the React app, and serves it with `npx serve`. For production use, see [TARGET_ARCHITECTURE_CONSTRAINTS.md](TARGET_ARCHITECTURE_CONSTRAINTS.md) for the target containerized Kubernetes deployment model.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the FINOS contribution process, governance model, and CLA requirements.

---

## License

Copyright 2023 UBS, FINOS, Morgan Stanley

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
