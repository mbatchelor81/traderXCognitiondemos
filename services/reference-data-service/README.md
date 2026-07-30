# Reference Data Service

S&P 500 reference data extracted from the TraderX monolith
(`traderx-monolith/app/routes/reference_data.py` and the stock helpers in
`traderx-monolith/app/utils/helpers.py`).

The service is stateless: the ticker catalogue is read once at startup from
`data/s-and-p-500-companies.csv` into an immutable in-memory structure. There is
no database and no outbound call to any peer service.

Every deployment serves exactly one tenant, fixed at startup by `TENANT_ID`.

## Run

```bash
python -m pip install -r requirements.txt
TENANT_ID=acme_corp python run.py     # listens on 0.0.0.0:8004
```

Starting without `TENANT_ID` fails fast with a clear error.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | `{"status": "UP", "service": "reference-data-service", "tenant": "<TENANT_ID>"}` |
| `GET` | `/` | Service metadata |
| `GET` | `/stocks/` | Full catalogue; optional `search` (case-insensitive substring of ticker or company name) and `limit` |
| `GET` | `/stocks/{ticker}` | One stock by exact ticker; **404** when unknown (the trading service treats 404 as "invalid security") |
| `GET` | `/openapi.json`, `/docs` | Generated OpenAPI spec and Swagger UI |

Responses use camelCase, matching the monolith:

```json
[{"ticker": "AAPL", "companyName": "Apple"}]
```

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TENANT_ID` | *(required)* | The single tenant this instance serves |
| `PORT` | `8004` | HTTP port |
| `HOST` | `0.0.0.0` | Bind address |
| `LOG_LEVEL` | `INFO` | Root log level |
| `REFERENCE_DATA_FILE` | `<service>/data/s-and-p-500-companies.csv` | Catalogue CSV, resolved relative to the service package |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `ACCOUNT_SERVICE_URL` | `http://localhost:8001` | Peer service URL (unused today) |
| `TRADING_SERVICE_URL` | `http://localhost:8002` | Peer service URL (unused today) |
| `POSITION_SERVICE_URL` | `http://localhost:8003` | Peer service URL (unused today) |
| `REFERENCE_DATA_SERVICE_URL` | `http://localhost:8004` | This service's own advertised URL |
| `PEOPLE_SERVICE_URL` | `http://localhost:8005` | Peer service URL (unused today) |

## Tenancy

- `TenantMiddleware` pins `request.state.tenant_id` to `TENANT_ID`.
- A request carrying `X-Tenant-ID` naming a different tenant gets **403**.
- A request with no tenant header is served for `TENANT_ID`.

## Observability

- Structured JSON logs on stdout, one object per line, each including
  `timestamp`, `level`, `message`, `service` and `tenant_id`.
- `X-Correlation-ID` is read from the request or generated, included in log
  lines, and echoed back on the response.
- Every request logs `method`, `path`, `status_code` and `duration_ms`.

## Tests

```bash
cd services/reference-data-service
python -m pytest tests/ -v
```

## Docker

The `Dockerfile` is a working placeholder; Process B hardens it (non-root user,
`HEALTHCHECK`, pinned base image).
