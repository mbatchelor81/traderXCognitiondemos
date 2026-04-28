# Skill: Add New Domain Service to TraderX Monolith

## When to use
When creating a new domain service module (model + service layer + API routes + tests) inside the TraderX monolith, following the extraction pattern defined in `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7.

## Prerequisites
- Python 3.12 installed
- `traderx-monolith/requirements.txt` dependencies installed (`pip install -r requirements.txt`)
- Existing tests passing: `cd traderx-monolith && python -m pytest tests/ -v`

## Steps

### 1. Create the SQLAlchemy model

Create `traderx-monolith/app/models/{domain}.py`:

- Import `Base` from `app.database` and `from app.config import *`
- Include a `tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)` column for multi-tenant filtering
- Include a `to_dict()` method that returns a dict with **camelCase** keys (matching frontend JSON conventions)
- Follow the pattern in `traderx-monolith/app/models/account.py` for structure

Example skeleton:

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from app.config import *  # noqa: F401,F403

class {Model}(Base):
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)
    # ... domain-specific columns ...

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            # ... camelCase keys for all fields ...
        }
```

Register the model in `traderx-monolith/app/models/__init__.py` by adding the import.

### 2. Create the service module

Create `traderx-monolith/app/services/{domain}_service.py`:

- Every function accepts `db: Session` and `tenant_id: str` as the first two arguments
- Always filter queries by `tenant_id`
- Use `log_audit_event()` from `app.utils.helpers` for create/update/delete operations
- Use `logging.getLogger(__name__)` for operational logs
- Follow the pattern in `traderx-monolith/app/services/account_service.py`

Standard functions to implement:

```python
def get_{entity}_by_id(db: Session, entity_id: int, tenant_id: str) -> Optional[{Model}]:
def get_all_{entities}(db: Session, tenant_id: str) -> List[{Model}]:
def create_{entity}(db: Session, ..., tenant_id: str) -> {Model}:
```

Register the service in `traderx-monolith/app/services/__init__.py`.

### 3. Create the route module

Create `traderx-monolith/app/routes/{domain}.py`:

- Define Pydantic request/response models at the top of the file (co-located, not in a separate schemas file)
- Use **camelCase** field names in Pydantic models to match frontend conventions
- Use `get_tenant_from_request(request)` for tenant extraction
- Use `Depends(get_db)` for database session injection
- Always call the service layer — do NOT write inline SQLAlchemy queries in route handlers
- Raise `HTTPException` for errors (404, 400)
- Return serialized data via `to_dict()`
- Follow the pattern in `traderx-monolith/app/routes/accounts.py`

Standard endpoints:

| Method | Path | Service Call |
|---|---|---|
| `GET /{domain}/` | List all for tenant | `service.get_all_{entities}(db, tenant_id)` |
| `GET /{domain}/{id}` | Get by ID | `service.get_{entity}_by_id(db, id, tenant_id)` |
| `POST /{domain}/` | Create | `service.create_{entity}(db, ..., tenant_id)` |

### 4. Register in main.py

Add the router to `traderx-monolith/app/main.py` inside the `create_app()` function:

```python
from app.routes.{domain} import router as {domain}_router
# ... inside create_app():
app.include_router({domain}_router, tags=["{Domain}"])
```

Place it after the existing `app.include_router()` calls (after line 110 in `main.py`).

### 5. Create tests

Create `traderx-monolith/tests/test_{domain}.py`:

- Use the `client` fixture from `conftest.py` (provides `TestClient` with in-memory SQLite)
- The `setup_database` fixture (autouse) creates/drops tables per test automatically
- Test the happy path for each endpoint (create → read → list)
- Test error cases (404 for missing resources, 422 for bad input)
- Set tenant header: `client.get("/...", headers={"X-Tenant-ID": "acme_corp"})`
- Follow the pattern in `traderx-monolith/tests/test_trade_submit.py`

### 6. Verify

```bash
cd traderx-monolith && python -m pytest tests/ -v
```

All tests must pass, including the new tests and all existing tests.

## Common Pitfalls

- **Circular imports:** Do not import from `trade_processor.py` in your service module. There is a known circular dependency between `trade_processor.py` and `account_service.py` — avoid extending this pattern. If you need trade data, accept it as a function parameter instead.
- **Missing `tenant_id` filter:** Every database query MUST filter by `tenant_id`. Omitting this leaks data across tenants. The `TenantMiddleware` in `app/middleware.py` injects it from the `X-Tenant-ID` header.
- **camelCase in Pydantic, snake_case in Python:** Pydantic request models use `camelCase` field names (e.g., `accountId`) to match the React frontend. SQLAlchemy models use `snake_case` (e.g., `account_id`). Map between them in the route handler.
- **Forgetting to register:** You must add the import and `include_router()` call in `main.py`, AND add the model import in `app/models/__init__.py`, AND add the service import in `app/services/__init__.py`. Missing any registration means the module exists but is not wired up.
- **`from app.config import *`:** Every model and service file must include this import. It provides `DEFAULT_TENANT` and other config values used in column defaults. Without it, `DEFAULT_TENANT` will be undefined.
