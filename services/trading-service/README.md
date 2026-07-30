# trading-service

Single-tenant trading domain service extracted from `traderx-monolith/`.
It owns trade submission and validation, the trade state machine, trade
analytics, and the Socket.io trade/position feed the frontend subscribes to.

**Owned table:** `trades` (and only that table). Accounts, positions, reference
data and people belong to their own services and are only reached over HTTP.

## Running

```bash
cd services/trading-service
python -m pip install -r requirements.txt
TENANT_ID=acme_corp python run.py     # http://localhost:8002
```

`TENANT_ID` is required — the process refuses to start without it. The tenant is
fixed at startup; there is no tenant switching. A request carrying an
`X-Tenant-ID` header naming a different tenant is rejected with `403`.

On first startup the service creates its tables and, if the `trades` table is
empty, seeds this tenant's demo trades.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/trade/` | Submit a trade — `{"accountId", "security", "side", "quantity"}` |
| `GET` | `/trades/` | All trades for this tenant, newest first |
| `GET` | `/trades/{account_id}` | Trades for one account |
| `GET` | `/analytics/trades` | Tenant-wide trade statistics |
| `GET` | `/analytics/trades/{account_id}` | Account trade statistics |
| `GET` | `/health` | `{"status": "UP", "service": "trading-service", "tenant": "<TENANT_ID>"}` |
| `GET` | `/openapi.json`, `/docs` | OpenAPI spec and Swagger UI |

`POST /trade/` returns `{"success", "error", "trade", "position"}`. Validation
failures return `400`; a peer service that is unreachable returns `502` — a
trade is never silently accepted.

### Socket.io

The Socket.io server is mounted on the same port (`8002`). Clients emit
`subscribe` / `unsubscribe` with a room name and receive `publish` events:

- `/accounts/{accountId}/trades` — trade updates
- `/accounts/{accountId}/positions` — position updates as reported by
  position-service

There is no tenant query parameter — one tenant per deployment.

## Trade processing flow

1. `GET {ACCOUNT_SERVICE_URL}/account/{id}/exists` — the account exists
2. `GET {ACCOUNT_SERVICE_URL}/accountuser/?accountId={id}` — it has ≥ 1 user
3. `GET {REFERENCE_DATA_SERVICE_URL}/stocks/{ticker}` — the ticker is real
4. Tenant business rules from config (`ALLOWED_SIDES`, `AUTO_SETTLE`)
5. Persist the trade and run the state machine
   (`New → Processing → Settled` when `AUTO_SETTLE` is on)
6. `POST {POSITION_SERVICE_URL}/positions/apply` with
   `{"accountId", "security", "quantityDelta"}` (Buy positive, Sell negative)
7. Publish `trade` and `position` updates over Socket.io

Selling more than the current position is allowed but logged as a warning —
this mirrors the monolith.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TENANT_ID` | *(required)* | The single tenant this instance serves |
| `DATABASE_URL` | `sqlite:///trades_{TENANT_ID}.db` | Trades database for this tenant |
| `HOST` / `PORT` | `0.0.0.0` / `8002` | Bind address |
| `LOG_LEVEL` | `INFO` | Root log level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `SOCKETIO_CORS_ALLOWED` | `*` | Socket.io allowed origins |
| `ACCOUNT_SERVICE_URL` | `http://localhost:8001` | Account existence and users |
| `POSITION_SERVICE_URL` | `http://localhost:8003` | Position reads and deltas |
| `REFERENCE_DATA_SERVICE_URL` | `http://localhost:8004` | Ticker validation |
| `PEER_REQUEST_TIMEOUT_SECONDS` | `5` | Timeout for peer HTTP calls |
| `ALLOWED_SIDES` | `Buy,Sell` | Sides this tenant may trade |
| `AUTO_SETTLE` | `true` | Settle trades immediately after the position applies |
| `MAX_ACCOUNTS` | `50` | Tenant account limit (reported in restrictions) |
| `MIN_TRADE_QUANTITY` / `MAX_TRADE_QUANTITY` | `1` / `1000000` | Quantity bounds |
| `AUDIT_ENABLED` | `true` | Emit audit log lines |

## Observability

- Structured JSON logs on stdout, one object per line, always carrying
  `timestamp`, `level`, `message`, `service`, `tenant_id` and — while serving a
  request — `correlation_id`.
- `X-Correlation-ID` is read from the request (or generated), echoed on the
  response, and forwarded on every outbound peer call.
- Every request is logged with `method`, `path`, `status_code` and `duration_ms`.
- `SIGTERM`/`SIGINT` drain in-flight requests; shutdown is logged.

## Tests

```bash
cd services/trading-service
python -m pytest tests/ -v
```

All cross-service calls are mocked — the suite passes with no peer service
running.

## Docker

The `Dockerfile` is a placeholder for Process B, which will add a non-root user
and a `HEALTHCHECK`.
