# TraderX Monolith (DEPRECATED)

> **DEPRECATION NOTICE**: This monolith application is the legacy reference implementation.
> It has been decomposed into independent single-tenant microservices under `services/`.
>
> **Do not add new features to this codebase.** All new development should target the
> extracted services.

## Migrated Services

| Service | Port | Directory |
|---------|------|-----------|
| Account Service | 8001 | `services/account-service/` |
| Trading Service | 8002 | `services/trading-service/` |
| Position Service | 8003 | `services/position-service/` |
| Reference Data Service | 8004 | `services/reference-data-service/` |
| People Service | 8005 | `services/people-service/` |

## Running the Migrated Services

Each service requires a `TENANT_ID` environment variable:

```bash
cd services/<service-name>
TENANT_ID=acme_corp python run.py
```

See `migration/MIGRATION_PLAN.md` for full migration details.

## Legacy Monolith (for reference only)

```bash
cd traderx-monolith
TENANT_ID=acme_corp python run.py
```

The monolith runs on port 8000 and serves all domains from a single process.
