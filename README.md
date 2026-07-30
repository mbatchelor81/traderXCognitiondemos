# TraderX — Single-Tenant Trading Platform

A trading platform decomposed into five single-tenant domain services (Python/FastAPI/SQLAlchemy)
with a React frontend. Every instance serves exactly one tenant, fixed at startup via `TENANT_ID`,
with its own database. The original monolith remains in [`traderx-monolith/`](traderx-monolith/)
as the deprecated legacy reference.

[![CI](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml/badge.svg)](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml)

---

## Prerequisites

- **Python 3.11+**
- **Node 18+**
- **npm**

---

## Services

| Service | Port | Owns | Depends on (HTTP) |
|---|---|---|---|
| [`account-service`](services/account-service) | 8001 | Accounts, account users, validation | position-service, people-service |
| [`trading-service`](services/trading-service) | 8002 | Trades, state machine, analytics, Socket.io feed | account-service, reference-data-service, position-service |
| [`position-service`](services/position-service) | 8003 | Positions, recalculation | — |
| [`reference-data-service`](services/reference-data-service) | 8004 | S&P 500 ticker lookup | — |
| [`people-service`](services/people-service) | 8005 | Person directory and validation | — |

Each service requires `TENANT_ID`, exposes `GET /health` →
`{"status": "UP", "service": "<name>", "tenant": "<TENANT_ID>"}`, serves its OpenAPI spec at
`/openapi.json` and `/docs`, and emits structured JSON logs.

---

## Quick Start

### 1. Start the services

```bash
for svc in account-service trading-service position-service reference-data-service people-service; do
  (cd services/$svc && pip install -r requirements.txt && TENANT_ID=acme_corp python run.py &)
done
```

### 2. Start the frontend

```bash
cd web-front-end/react
npm install
REACT_APP_TENANT_ID=acme_corp npm start
```

The UI will be available at `http://localhost:3000`. The tenant is a **build-time** constant —
rebuild to serve a different tenant.

### 3. Run the cross-service integration test

```bash
TENANT_ID=test_tenant python tests/integration/test_cross_service.py
```

---

## Configuration

| Variable | Applies to | Default | Description |
|---|---|---|---|
| `TENANT_ID` | every service | — (**required**, fails fast) | The single tenant this instance serves |
| `DATABASE_URL` | services with a database | `sqlite:///<domain>_<TENANT_ID>.db` | Tenant-specific database |
| `PORT` / `HOST` | every service | service port / `0.0.0.0` | Listen address |
| `ACCOUNT_SERVICE_URL` | trading-service | `http://localhost:8001` | Peer service URL |
| `TRADING_SERVICE_URL` | frontend | `http://localhost:8002` | Peer service URL |
| `POSITION_SERVICE_URL` | account-service, trading-service | `http://localhost:8003` | Peer service URL |
| `REFERENCE_DATA_SERVICE_URL` | trading-service | `http://localhost:8004` | Peer service URL |
| `PEOPLE_SERVICE_URL` | account-service | `http://localhost:8005` | Peer service URL |
| `REACT_APP_TENANT_ID` | frontend | — (**required at build time**) | Tenant baked into the bundle |

A request carrying an `X-Tenant-ID` header that names a different tenant is rejected with `403`.

---

## Architecture

- **[TARGET_ARCHITECTURE_CONSTRAINTS.md](TARGET_ARCHITECTURE_CONSTRAINTS.md)** — the authority for the target state
- **[migration/MIGRATION_PLAN.md](migration/MIGRATION_PLAN.md)** — current → target migration, service boundaries, URL mapping
- **[migration/DEFINITION_OF_DONE.md](migration/DEFINITION_OF_DONE.md)** — migration checklist (Process A done, Process B pending)
- **[LEGACY_ARCHITECTURE.md](LEGACY_ARCHITECTURE.md)** — the legacy monolith's architecture and anti-patterns
- **[traderx-monolith/](traderx-monolith/)** — deprecated legacy reference implementation

---

## License

Copyright 2023 UBS, FINOS, Morgan Stanley

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
