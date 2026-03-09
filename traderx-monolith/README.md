# TraderX Monolith (DEPRECATED)

> **DEPRECATION NOTICE**: This monolith is the legacy reference implementation.
> It has been decomposed into independent single-tenant services under `../services/`.
>
> **Migrated services:**
> | Service | Port | Directory |
> |---------|------|-----------|
> | Account Service | 8001 | `services/account-service/` |
> | Trading Service | 8002 | `services/trading-service/` |
> | Position Service | 8003 | `services/position-service/` |
> | Reference Data Service | 8004 | `services/reference-data-service/` |
> | People Service | 8005 | `services/people-service/` |
>
> See `migration/MIGRATION_PLAN.md` for full details.

## Overview

The TraderX monolith is a Python/FastAPI application that provides account management,
trade processing, position tracking, reference data, and people directory services.

## Prerequisites

- Python 3.10+
- pip

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
TENANT_ID=acme_corp python run.py
```

The application requires `TENANT_ID` environment variable at startup.

## Testing

```bash
TENANT_ID=acme_corp python -m pytest tests/ -v
```
