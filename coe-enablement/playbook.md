# Playbook: Extract Domain Service from TraderX Monolith

## Goal
Extract a complete domain service from the TraderX monolith — including the service module, API routes, tests, observability instrumentation, and a Dockerfile — following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §3, §7, and §10.

## Inputs
- **service_name**: The lowercase service name (e.g., `position`, `notification`, `audit`)
- **domain**: The business domain label (e.g., `Positions`, `Notifications`, `Audit`)
- **model_columns**: Column definitions for the SQLAlchemy model (name, type, constraints)
- **service_functions**: List of service-layer functions to implement (e.g., `create_X`, `get_X_by_id`, `list_all_X`)
- **endpoints**: List of API endpoints with HTTP methods and paths

## Steps

### Step 1: Discover — Audit Current State
- **Tool:** Ask Devin (lightweight session)
- **Prompt:** "Scan `traderx-monolith/app/` and list all existing route modules, service modules, and models. Which domains from `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7 are already implemented vs. missing?"
- **Expected output:** A table showing implemented vs. planned services, with file paths for each existing module.
- **Validation:** The response references `app/routes/accounts.py`, `app/routes/trades.py`, `app/routes/positions.py`, `app/routes/people.py`, `app/routes/reference_data.py` and identifies any gaps against the 5 target services (Account, Trading, Position, Reference Data, People).

### Step 2: Scope — Generate Extraction Plan
- **Tool:** Ask Devin (lightweight session)
- **Prompt:** "For the `{service_name}` service, generate a file-by-file extraction plan. List every file to create or modify, with the expected content structure for each."
- **Expected output:** A numbered list of files (model, service, routes, `__init__.py` registrations, tests) with one-line descriptions of what each file contains.
- **Validation:** Plan includes all 5 file categories: model, service, routes, main.py registration, tests. No placeholder paths — all paths are under `traderx-monolith/`.

### Step 3: Scaffold the Service Module (sub-agent)
- **Tool:** Devin Cloud (sub-session)
- **Prompt:** "Use the `add-new-service` skill in `.agents/skills/add-new-service/SKILL.md` to create the `{service_name}` service. Model columns: {model_columns}. Service functions: {service_functions}. Endpoints: {endpoints}. Run `python -m pytest tests/ -v` and confirm all tests pass."
- **Expected output:** PR with new files: `app/models/{service_name}.py`, `app/services/{service_name}_service.py`, `app/routes/{service_name}.py`, `tests/test_{service_name}.py`, plus modifications to `app/main.py`, `app/models/__init__.py`, `app/services/__init__.py`.
- **Validation:**
  - `python -m pytest tests/ -v` passes (all existing + new tests)
  - New model includes `tenant_id` column with `DEFAULT_TENANT` default
  - New routes use `get_tenant_from_request()` and `Depends(get_db)`
  - Pydantic models use camelCase field names

### Step 4: Add Observability (sub-agent)
- **Tool:** Devin Cloud (sub-session)
- **Prompt:** "Use the `add-observability-to-service` skill in `.windsurf/skills/add-observability-to-service/SKILL.md` to add structured logging, a health check, and request timing to the `{service_name}` service module at `traderx-monolith/app/services/{service_name}_service.py`. Run tests to verify."
- **Expected output:** Structured JSON logging in the service module, correlation ID support, updated health check verifying DB connectivity.
- **Validation:**
  - All log statements in `{service_name}_service.py` use structured format with `tenant_id` and `entity_id` fields
  - `python -m pytest tests/ -v` still passes
  - `curl http://localhost:8000/health` returns `{"status": "healthy", "database": "connected"}`

### Step 5: Add Integration Tests (sub-agent)
- **Tool:** Devin Cloud (sub-session)
- **Prompt:** "Use the `add-integration-test` skill in `.windsurf/skills/add-integration-test/SKILL.md` to add comprehensive integration tests for the `{service_name}` service. Cover: CRUD happy paths, 404 on missing resource, multi-tenant isolation (create in tenant A, verify invisible in tenant B), and input validation (422 on bad input)."
- **Expected output:** Expanded test file at `tests/test_{service_name}.py` with 6+ test cases.
- **Validation:**
  - `python -m pytest tests/test_{service_name}.py -v` shows 6+ tests passing
  - At least one test verifies tenant isolation by querying with a different `X-Tenant-ID` header
  - At least one test verifies 404 for non-existent resource

### Step 6: Create Dockerfile
- **Tool:** Windsurf / Chisel (local or CLI)
- **Action:** Create `traderx-monolith/Dockerfile` following `TARGET_ARCHITECTURE_CONSTRAINTS.md` §3:
  ```dockerfile
  FROM python:3.12-slim
  RUN useradd --create-home appuser
  WORKDIR /home/appuser/app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  USER appuser
  HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
  EXPOSE 8000
  CMD ["uvicorn", "app.main:combined_app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **Validation:**
  - `docker build -t traderx-monolith .` succeeds
  - `docker run -p 8000:8000 traderx-monolith` starts and `curl http://localhost:8000/health` returns `{"status": "UP"}`
  - Container runs as non-root user (`appuser`)

## Success Criteria
- All `python -m pytest tests/ -v` tests pass (existing + new)
- New service module follows the same structure as `account_service.py` and `accounts.py`
- Every database query filters by `tenant_id`
- No new circular imports introduced (verify: `python -c "from app.services.{service_name}_service import *"` succeeds without ImportError)
- Dockerfile builds and runs with health check passing
- PR created with clear description referencing `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7
