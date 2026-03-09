# TraderX Monolith (DEPRECATED)

> **DEPRECATED**: This is the legacy monolith reference implementation. Use the `services/` directory for the migrated single-tenant services:
> - `services/users-service/` — Accounts, account-users, people directory (port 8001)
> - `services/trades-service/` — Trades, positions, reference data, Socket.IO real-time (port 8002)

## Overview

This directory contains the original Python/FastAPI monolith that served all TraderX functionality from a single process on port 8000. It has been superseded by the extracted domain services.

## Running (Legacy)

```bash
# Requires TENANT_ID environment variable
TENANT_ID=acme_corp python run.py
```

The monolith starts on port 8000. It requires `TENANT_ID` to be set at startup.

## Tests (Legacy)

```bash
TENANT_ID=acme_corp python -m pytest tests/ -v
```

## Migration

See `migration/MIGRATION_PLAN.md` for the full migration plan and `migration/DEFINITION_OF_DONE.md` for the completion checklist.
