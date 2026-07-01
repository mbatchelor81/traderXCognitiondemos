---
name: add-fastapi-endpoint
description: Add a new REST endpoint to the TraderX Python monolith following team conventions for route structure, Pydantic validation, tenant extraction, logging, error handling, and service-layer delegation.
---

# Add a FastAPI Endpoint to TraderX Monolith

Use this skill when adding a new REST endpoint to the TraderX Python monolith (`traderx-monolith/`).

## 1. Determine the Route File

1. Identify which domain the endpoint belongs to (accounts, trades, positions, people, reference data, or a new domain).
2. If an existing route file in `traderx-monolith/app/routes/` covers the domain, add the endpoint there.
3. If a new route file is needed:
   - Create `traderx-monolith/app/routes/<domain>.py`.
   - Add a module-level docstring describing the file's purpose.
   - Add the standard imports and scaffolding (see step 2 below).
   - Register the new router in `traderx-monolith/app/main.py` inside `create_app()`:
     ```python
     from app.routes import <domain>
     app.include_router(<domain>.router, tags=["<DomainName>"])
     ```

## 2. Set Up Imports and Module Scaffolding

Every route file must start with these imports (include only what the endpoint needs):

```python
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.models.<model_module> import <Model>
from app.services import <service_module>
from app.utils.helpers import get_tenant_from_request

logger = logging.getLogger(__name__)

router = APIRouter()
```

## 3. Define Pydantic Request/Response Models

1. Add Pydantic `BaseModel` classes for any request body or structured response above the endpoint function.
2. Group them under a section comment:
   ```python
   # =============================================================================
   # Pydantic Request/Response Models
   # =============================================================================
   ```
3. Use `Optional` fields with defaults for optional parameters.
4. Use `camelCase` field names to match the existing frontend conventions (e.g., `accountId`, `displayName`).

Example:

```python
class MyRequestBody(BaseModel):
    accountId: int
    description: Optional[str] = None
```

## 4. Write the Endpoint Function

1. Decorate with `@router.get(...)`, `@router.post(...)`, `@router.put(...)`, or `@router.delete(...)` using the appropriate path.
2. Include a descriptive docstring on the function explaining the endpoint's purpose.
3. Use `Depends(get_db)` for database session injection and accept `request: Request` for tenant extraction.

Endpoint function signature pattern:

```python
@router.post("/myresource/")
def create_my_resource(body: MyRequestBody, request: Request,
                       db: Session = Depends(get_db)):
    """Create a new resource for the current tenant."""
```

For `GET` endpoints without a request body:

```python
@router.get("/myresource/")
def list_my_resources(request: Request, db: Session = Depends(get_db)):
    """List all resources for the current tenant."""
```

## 5. Extract the Tenant

As the first line inside the endpoint function body, extract the tenant:

```python
tenant_id = get_tenant_from_request(request)
```

## 6. Add Logging at INFO Level

Log the endpoint entry at `INFO` level immediately after tenant extraction. Include relevant parameters:

```python
logger.info("Creating resource: account=%d description=%s tenant=%s",
            body.accountId, body.description, tenant_id)
```

## 7. Delegate Business Logic to the Service Layer

1. Do **not** put business logic inline in the route function. Keep the route thin.
2. Call an existing service function in `traderx-monolith/app/services/` or create a new one.
3. Service functions follow the convention: `def my_function(db: Session, ..., tenant_id: str)`.
4. If adding a new service file:
   - Create `traderx-monolith/app/services/<service_name>.py`.
   - Add `import logging` and `logger = logging.getLogger(__name__)`.
   - Import models and helpers as needed.
   - Include a module-level docstring.

Example service call from the route:

```python
result = my_service.do_something(db, body.accountId, tenant_id)
```

## 8. Add Error Handling with HTTPException

1. Validate inputs and raise `HTTPException` with appropriate status codes:
   - `400` for bad requests / validation failures
   - `404` for resources not found
   - `409` for conflicts
   - `500` for unexpected server errors (wrap in try/except if calling external logic)
2. Always provide a descriptive `detail` message.

```python
if result is None:
    raise HTTPException(status_code=404,
                        detail=f"Resource {resource_id} not found")
```

3. For unexpected errors, use a try/except:

```python
try:
    result = my_service.do_something(db, body.accountId, tenant_id)
except Exception as e:
    logger.error("Failed to create resource: %s", str(e))
    raise HTTPException(status_code=500,
                        detail="Internal error while creating resource")
```

## 9. Return the Response

1. Use the model's `.to_dict()` method for single objects: `return result.to_dict()`
2. Use a list comprehension for collections: `return [r.to_dict() for r in results]`

## 10. Run Tests

Run the test suite from the `traderx-monolith` directory to verify nothing is broken:

```bash
cd traderx-monolith && python -m pytest tests/ -v
```

All existing tests must continue to pass.
