"""
Billing stored query endpoints.
Provides CRUD and execution for versioned, parameterized billing queries.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.database import get_db
from app.services.stored_query_service import (
    QueryNotFoundError,
    UnsupportedQueryTypeError,
    delete_query,
    execute_query,
    get_query,
    list_queries,
    register_query,
    seed_billing_queries,
)
from app.utils.helpers import get_tenant_from_request

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class StoredQueryRegister(BaseModel):
    description: Optional[str] = None
    queryType: str = Field(max_length=100)
    queryDefinition: dict[str, Any]
    parametersSchema: Optional[dict[str, Any]] = None


class StoredQueryExecute(BaseModel):
    parameters: Optional[dict[str, Any]] = None


# =============================================================================
# Stored Query Endpoints
# =============================================================================

@router.get("/query")
def list_stored_queries(request: Request, db: Session = Depends(get_db)):
    """List all registered stored queries for the current tenant."""
    tenant_id = get_tenant_from_request(request)
    queries = list_queries(db, tenant_id)
    return [q.to_dict() for q in queries]


@router.put("/query/{qualified_query_name}/{version}")
def register_stored_query(
    qualified_query_name: str,
    version: str,
    body: StoredQueryRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register or update a stored query definition."""
    tenant_id = get_tenant_from_request(request)
    sq = register_query(
        db=db,
        qualified_name=qualified_query_name,
        version=version,
        query_type=body.queryType,
        query_definition=body.queryDefinition,
        tenant_id=tenant_id,
        description=body.description,
        parameters_schema=body.parametersSchema,
    )
    return sq.to_dict()


@router.get("/query/{qualified_query_name}/{version}")
def get_stored_query(
    qualified_query_name: str,
    version: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Retrieve a stored query definition by name and version."""
    tenant_id = get_tenant_from_request(request)
    sq = get_query(db, qualified_query_name, version, tenant_id)
    if sq is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stored query {qualified_query_name}/{version} not found",
        )
    return sq.to_dict()


@router.post("/query/{qualified_query_name}/{version}")
def execute_stored_query(
    qualified_query_name: str,
    version: str,
    body: Optional[StoredQueryExecute] = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """Execute a stored query with optional parameters."""
    tenant_id = get_tenant_from_request(request)
    params = body.parameters if body else None
    try:
        result = execute_query(
            db=db,
            qualified_name=qualified_query_name,
            version=version,
            tenant_id=tenant_id,
            parameters=params,
        )
    except QueryNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Stored query {qualified_query_name}/{version} not found",
        )
    except UnsupportedQueryTypeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    return result


@router.post("/query/_seed")
def seed_queries(request: Request, db: Session = Depends(get_db)):
    """Seed the pre-built billing queries for the current tenant."""
    tenant_id = get_tenant_from_request(request)
    registered = seed_billing_queries(db, tenant_id)
    return {
        "seeded": len(registered),
        "queries": [q.to_dict() for q in registered],
    }
