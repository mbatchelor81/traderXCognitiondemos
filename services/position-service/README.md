# position-service

Position tracking, position queries and position recalculation for **one tenant**.
Extracted from `traderx-monolith` (`app/models/position.py`, `app/routes/positions.py`,
and the position logic in `app/services/trade_processor.py`).

This service owns the `positions` table and is its only reader and writer. It has **no
outbound dependencies** on other services — everyone else calls it.

## Run it

```bash
cd services/position-service
python -m pip install -r requirements.txt
TENANT_ID=acme_corp python run.py     # http://localhost:8003
```

`run.py` creates the tables, seeds the tenant's demo positions when the database is
empty, then serves until `SIGTERM`/`SIGINT`, draining in-flight requests before exit.

Starting without `TENANT_ID` fails immediately:

```
RuntimeError: TENANT_ID environment variable is required. Each instance serves exactly one tenant.
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TENANT_ID` | — (**required**) | The single tenant this instance serves |
| `DATABASE_URL` | `sqlite:///positions_<TENANT_ID>.db` | Tenant-owned position database |
| `DATABASE_ECHO` | `false` | Echo SQL statements |
| `PORT` | `8003` | Listen port |
| `HOST` | `0.0.0.0` | Listen address |
| `LOG_LEVEL` | `INFO` | Root log level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `AUDIT_ENABLED` | `true` | Emit audit log lines for position mutations |
| `POSITION_SERVICE_URL` | `http://localhost:8003` | This service's own published URL |

No credentials are hardcoded anywhere.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | `{"status": "UP", "service": "position-service", "tenant": "<TENANT_ID>"}`; `503` + `"DOWN"` when the database is unreachable |
| `GET` | `/` | Service banner |
| `GET` | `/positions/` | All positions for the tenant |
| `GET` | `/positions/{account_id}` | Positions for one account (unknown account → `[]`) |
| `POST` | `/positions/apply` | Apply a quantity delta; creates the position when absent |
| `POST` | `/positions/recalculate` | Recompute an account's positions from caller-supplied trades |
| `GET` | `/openapi.json`, `/docs` | Generated OpenAPI spec and Swagger UI |

### `POST /positions/apply`

```json
{"accountId": 22214, "security": "AAPL", "quantityDelta": -30}
```

```json
{"accountId": 22214, "tenant_id": "acme_corp", "security": "AAPL", "quantity": 70,
 "updated": "2026-07-30T12:00:00.000000"}
```

Upserts on `(account_id, security, tenant_id)` and adds the delta to the existing
quantity. Negative resulting quantities are allowed (the monolith permits short
positions). Not idempotent — each call applies the delta again.

### `POST /positions/recalculate`

```json
{"accountId": 22214,
 "trades": [{"security": "AAPL", "side": "Buy", "quantity": 100},
            {"security": "AAPL", "side": "Sell", "quantity": 30}]}
```

Returns the recomputed positions. Positions are recomputed **only** from the trades the
caller supplies — this service owns no trades table. Securities absent from the supplied
trades are left untouched, matching the monolith's `recalculate_positions`.

## Tenancy

The tenant is fixed at startup. `TenantMiddleware` sets `request.state.tenant_id` on
every request and returns **403** when an `X-Tenant-ID` header names a different tenant.
A request with no tenant header is served for `TENANT_ID`. Every row stores `tenant_id`
and every query filters on it, on top of the per-tenant database.

## Observability

Structured JSON logs on stdout, one object per line, each including `timestamp`,
`level`, `message`, `service` and `tenant_id`. `CorrelationIdMiddleware` reads or
generates `X-Correlation-ID`, exposes it on `request.state` and echoes it in the
response header; `RequestTimingMiddleware` logs `method`, `path`, `status_code` and
`duration_ms` per request.

## Tests

```bash
cd services/position-service
python -m pytest tests/ -v
```

`tests/conftest.py` sets `TENANT_ID=test_tenant` before importing any application
module and binds an in-memory SQLite session through `app.dependency_overrides`.

## Docker

`Dockerfile` is a minimal placeholder for Process B, which hardens it (non-root user,
`HEALTHCHECK`).
