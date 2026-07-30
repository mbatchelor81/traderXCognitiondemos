# account-service

Accounts, account-user membership, and account validation, extracted from the
TraderX monolith. This service is the only reader and writer of the `accounts`
and `account_users` tables.

One process serves exactly one tenant: `TENANT_ID` is required at startup and
there is no tenant switching at runtime. A request carrying an `X-Tenant-ID`
header naming a different tenant is rejected with HTTP 403.

## Run it

```bash
cd services/account-service
python -m pip install -r requirements.txt
TENANT_ID=acme_corp python run.py     # http://localhost:8001
```

On first startup the tables are created and, if the database is empty, the
tenant's accounts are seeded: `22214 "Test Account 20"` and
`11413 "Private Clients Fund TTXX"`, with users `jsmith`, `jdoe` and
`mwilliams`.

## Tests

```bash
cd services/account-service
python -m pytest tests/ -v
```

All cross-service HTTP calls are mocked, so no peer service needs to be running.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/account/` | List accounts |
| POST | `/account/` | Create an account (`{"id"?: int, "displayName": str}`) |
| PUT | `/account/` | Update an account |
| GET | `/account/{account_id}` | One account, with `positions` fetched from position-service |
| GET | `/account/{account_id}/exists` | `{"exists": bool}` — cheap validation for trading-service |
| GET | `/accountuser/` | List account users; optional `?accountId=` filter |
| POST | `/accountuser/` | Add a user (`{"accountId": int, "username": str}`), validated against people-service |
| PUT | `/accountuser/` | Update an account user |
| GET | `/health` | `{"status": "UP", "service": "account-service", "tenant": "<TENANT_ID>"}` |
| GET | `/openapi.json`, `/docs` | Generated OpenAPI spec and Swagger UI |

JSON payloads keep the monolith's camelCase keys so the existing frontend works
unchanged.

## Cross-service dependencies

| Peer | Env var (default) | Used by | On failure |
|---|---|---|---|
| position-service | `POSITION_SERVICE_URL` (`http://localhost:8003`) | `GET /account/{account_id}` → `GET /positions/{account_id}` | Log a warning and return `"positions": []` |
| people-service | `PEOPLE_SERVICE_URL` (`http://localhost:8005`) | `POST /accountuser/` → `GET /people/ValidatePerson?LogonId=` | HTTP 503; the membership row is not written |

Outbound calls time out after `PEER_TIMEOUT_SECONDS` (default 2s) and propagate
`X-Correlation-ID` and `X-Tenant-ID`.

account-service has no dependency on trading-service. The monolith's
`get_trade_count_for_account` / `can_delete_account` helpers were dropped —
trade counts belong to trading-service.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TENANT_ID` | *(required — startup fails without it)* | The single tenant this instance serves |
| `DATABASE_URL` | `sqlite:///accounts_<TENANT_ID>.db` | Per-tenant database |
| `DATABASE_ECHO` | `false` | SQLAlchemy statement logging |
| `HOST` / `PORT` | `0.0.0.0` / `8001` | Bind address |
| `LOG_LEVEL` | `INFO` | Root log level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `POSITION_SERVICE_URL` | `http://localhost:8003` | position-service base URL |
| `PEOPLE_SERVICE_URL` | `http://localhost:8005` | people-service base URL |
| `ACCOUNT_SERVICE_URL` / `TRADING_SERVICE_URL` / `REFERENCE_DATA_SERVICE_URL` | `http://localhost:8001` / `:8002` / `:8004` | Declared for completeness; not called |
| `PEER_TIMEOUT_SECONDS` | `2` | Timeout for outbound peer calls |

No credentials are baked into the image or the source.

## Observability

Structured JSON logs go to stdout, one object per line, each carrying
`timestamp`, `level`, `message`, `service`, `tenant_id` and — for anything
logged while serving a request — `correlation_id`. `CorrelationIdMiddleware`
accepts or generates `X-Correlation-ID` and echoes it back;
`RequestTimingMiddleware` logs `method`, `path`, `status_code` and
`duration_ms` for every request.

## Shutdown

`run.py` relies on uvicorn's SIGTERM/SIGINT handling: the server stops accepting
connections, in-flight requests drain (30s grace), the FastAPI lifespan logs
`shutting down`, and the process exits cleanly.

## Docker

The `Dockerfile` is a minimal placeholder — Process B hardens it (non-root user,
`HEALTHCHECK`, pinned base image).
