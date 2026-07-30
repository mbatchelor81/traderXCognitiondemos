# people-service

The TraderX person directory and person validation service, extracted from
`traderx-monolith`. One process serves exactly one tenant.

The directory is a static JSON file (`data/people.json`) loaded once at startup
into an immutable tuple — there is no database and no outbound service call.

## Run

```bash
cd services/people-service
python -m pip install -r requirements.txt
TENANT_ID=acme_corp python run.py      # listens on 0.0.0.0:8005
```

`TENANT_ID` is required: the process refuses to start without it, even though
the service is stateless.

`run.py` starts uvicorn, which handles `SIGTERM`/`SIGINT` by refusing new
connections, draining in-flight requests (30s grace) and running the FastAPI
shutdown hook, which logs `shutting down`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "UP", "service": "people-service", "tenant": "<TENANT_ID>"}` |
| GET | `/` | Service identity |
| GET | `/people/GetPerson?LogonId=<id>&EmployeeId=<id>` | One person; 404 when unknown, 400 when neither identifier is given |
| GET | `/people/GetMatchingPeople?SearchText=<text>&Take=<n>` | `{"People": [...]}`; 400 when `SearchText` is missing or shorter than 3 characters |
| GET | `/people/ValidatePerson?LogonId=<id>&EmployeeId=<id>` | `{"IsValid": true\|false}` — the contract account-service calls when creating an account user |
| GET | `/openapi.json`, `/docs` | Generated OpenAPI spec and Swagger UI |

Person payloads keep the monolith's PascalCase keys:
`LogonId`, `FullName`, `Email`, `EmployeeId`, `Department`, `PhotoUrl`.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TENANT_ID` | *(required)* | The single tenant this instance serves |
| `PORT` | `8005` | Listen port |
| `HOST` | `0.0.0.0` | Listen address |
| `LOG_LEVEL` | `INFO` | Root log level |
| `PEOPLE_DATA_FILE` | `<service>/data/people.json` | Directory data file, resolved relative to the package |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `ACCOUNT_SERVICE_URL` | `http://localhost:8001` | Peer URL (unused today) |
| `TRADING_SERVICE_URL` | `http://localhost:8002` | Peer URL (unused today) |
| `POSITION_SERVICE_URL` | `http://localhost:8003` | Peer URL (unused today) |
| `REFERENCE_DATA_SERVICE_URL` | `http://localhost:8004` | Peer URL (unused today) |
| `PEOPLE_SERVICE_URL` | `http://localhost:8005` | This service's own advertised URL |

## Tenancy

`TenantMiddleware` pins `request.state.tenant_id` to `TENANT_ID` and returns
**403** when a request carries an `X-Tenant-ID` header naming a different
tenant. A request with no tenant header is served for `TENANT_ID`.

## Observability

- Structured JSON logs on stdout, one object per line, always including
  `timestamp`, `level`, `message`, `service` and `tenant_id`.
- `CorrelationIdMiddleware` reads or generates `X-Correlation-ID`, exposes it on
  `request.state.correlation_id` and echoes it on the response.
- `RequestTimingMiddleware` logs `method`, `path`, `status_code` and
  `duration_ms` for every request.

## Tests

```bash
cd services/people-service
python -m pytest tests/ -v
```
