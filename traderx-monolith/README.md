# TraderX Monolith (DEPRECATED)

> **DEPRECATION NOTICE**: This monolith is the legacy reference implementation.
> It has been migrated to single-tenant, service-extracted architecture.
>
> The actively maintained services are located at:
> - `services/users-service/` — Account management, account-users, people directory (port 8001)
> - `services/trades-service/` — Trade processing, positions, reference data, Socket.IO (port 8002)
>
> See `migration/MIGRATION_PLAN.md` for details on the migration.

## Original Description

Monolithic Python/FastAPI backend that consolidated all TraderX microservices
(account-service, trade-service, trade-processor, position-service, people-service,
reference-data) into a single deployable unit with a shared SQLite database.

## Running (Legacy)

```bash
TENANT_ID=acme_corp python run.py
```

Requires `TENANT_ID` environment variable to be set at startup.
