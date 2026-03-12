# TraderX — Legacy Trading Platform

A multi-tenant trading platform built as a Python/FastAPI monolith. Supports account management, trade submission, position tracking, and real-time updates via Socket.io. Uses SQLite for storage with 3 demo tenants (`acme_corp`, `globex_inc`, `initech`).

[![CI](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml/badge.svg)](https://github.com/mbatchelor81/traderXCognitiondemos/actions/workflows/ci.yml)

---

## Prerequisites

- **Python 3.11+**
- **Node 18+**
- **npm**

---

## Quick Start

### 1. Start the backend

```bash
cd traderx-monolith
pip install -r requirements.txt
python run.py
```

The API will be available at `http://localhost:8000`.

### 2. Start the frontend

```bash
cd web-front-end/react
npm install
npm start
```

The UI will be available at `http://localhost:3000`.

### 3. Open the app

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/account/` | List all accounts for the current tenant |
| `POST` | `/account/` | Create a new account |
| `PUT` | `/account/` | Update an existing account |
| `GET` | `/account/{account_id}` | Get account by ID with portfolio summary |
| `GET` | `/accountuser/` | List all account users |
| `POST` | `/accountuser/` | Create a new account user |
| `PUT` | `/accountuser/` | Update an account user |
| `POST` | `/trade/` | Submit a new trade order |
| `GET` | `/trades/` | List all trades for the current tenant |
| `GET` | `/trades/{account_id}` | List trades for a specific account |
| `GET` | `/positions/` | List all positions for the current tenant |
| `GET` | `/positions/{account_id}` | List positions for a specific account |
| `GET` | `/stocks/` | List all S&P 500 stocks |
| `GET` | `/stocks/{ticker}` | Get stock by ticker symbol |
| `GET` | `/people/GetPerson` | Get a person by LogonId or EmployeeId |
| `GET` | `/people/GetMatchingPeople` | Search for people matching text |
| `GET` | `/people/ValidatePerson` | Validate that a person exists |
| `GET` | `/health` | Health check |

---

## Multi-Tenant

TraderX supports multiple tenants via the `X-Tenant-ID` HTTP header. If the header is not provided, the default tenant (`acme_corp`) is used.

### Available Tenants

| Tenant ID | Description |
|---|---|
| `acme_corp` | 2 accounts, 8 trades, 7 positions |
| `globex_inc` | 2 accounts, 5 trades, 5 positions |
| `initech` | 3 accounts, 8 trades, 7 positions |

### Example

```bash
# List accounts for the default tenant (acme_corp)
curl http://localhost:8000/account/

# List accounts for a specific tenant
curl -H "X-Tenant-ID: globex_inc" http://localhost:8000/account/
```

---

## Architecture

This is a legacy monolithic application with known technical debt. See the following documents for details:

- **[LEGACY_ARCHITECTURE.md](LEGACY_ARCHITECTURE.md)** — Current system architecture, database schema, module coupling, and known anti-patterns
- **[TARGET_ARCHITECTURE_CONSTRAINTS.md](TARGET_ARCHITECTURE_CONSTRAINTS.md)** — Target state requirements and constraints for a future migration to microservices

---

## License

Copyright 2023 UBS, FINOS, Morgan Stanley

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
