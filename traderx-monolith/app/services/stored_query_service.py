"""
Stored query registry service.
Manages versioned, parameterized query definitions for billing data extraction.
Queries are registered with a qualified name + version and executed against the
application's data model to produce structured billing-relevant results.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.models.account import Account, AccountUser
from app.models.position import Position
from app.models.stored_query import StoredQuery
from app.models.trade import Trade
from app.utils.helpers import log_audit_event

logger = logging.getLogger(__name__)


# =============================================================================
# Query CRUD
# =============================================================================

def register_query(
    db: Session,
    qualified_name: str,
    version: str,
    query_type: str,
    query_definition: dict[str, Any],
    tenant_id: str,
    description: Optional[str] = None,
    parameters_schema: Optional[dict[str, Any]] = None,
) -> StoredQuery:
    """Register or update a stored query definition."""
    existing = get_query(db, qualified_name, version, tenant_id)
    if existing is not None:
        existing.description = description
        existing.query_type = query_type
        existing.query_definition = json.dumps(query_definition)
        existing.parameters_schema = (
            json.dumps(parameters_schema) if parameters_schema else None
        )
        db.commit()
        db.refresh(existing)
        log_audit_event(
            "STORED_QUERY_UPDATED", tenant_id,
            f"name={qualified_name} version={version}",
        )
        logger.info("Updated stored query %s/%s for tenant %s",
                     qualified_name, version, tenant_id)
        return existing

    stored_query = StoredQuery(
        qualified_name=qualified_name,
        version=version,
        description=description,
        query_type=query_type,
        query_definition=json.dumps(query_definition),
        parameters_schema=(
            json.dumps(parameters_schema) if parameters_schema else None
        ),
        tenant_id=tenant_id,
        created_at=datetime.utcnow(),
    )
    db.add(stored_query)
    db.commit()
    db.refresh(stored_query)
    log_audit_event(
        "STORED_QUERY_REGISTERED", tenant_id,
        f"name={qualified_name} version={version}",
    )
    logger.info("Registered stored query %s/%s for tenant %s",
                 qualified_name, version, tenant_id)
    return stored_query


def get_query(
    db: Session,
    qualified_name: str,
    version: str,
    tenant_id: str,
) -> Optional[StoredQuery]:
    """Retrieve a stored query by qualified name, version, and tenant."""
    return db.query(StoredQuery).filter(
        StoredQuery.qualified_name == qualified_name,
        StoredQuery.version == version,
        StoredQuery.tenant_id == tenant_id,
    ).first()


def list_queries(db: Session, tenant_id: str) -> list[StoredQuery]:
    """List all stored queries for a tenant."""
    return db.query(StoredQuery).filter(
        StoredQuery.tenant_id == tenant_id,
    ).all()


def delete_query(
    db: Session,
    qualified_name: str,
    version: str,
    tenant_id: str,
) -> bool:
    """Delete a stored query. Returns True if found and deleted."""
    query = get_query(db, qualified_name, version, tenant_id)
    if query is None:
        return False
    db.delete(query)
    db.commit()
    log_audit_event(
        "STORED_QUERY_DELETED", tenant_id,
        f"name={qualified_name} version={version}",
    )
    return True


# =============================================================================
# Query Execution
# =============================================================================

def execute_query(
    db: Session,
    qualified_name: str,
    version: str,
    tenant_id: str,
    parameters: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Execute a stored query with the given parameters.

    Dispatches to the appropriate handler based on ``query_type`` and returns
    structured results.
    """
    stored = get_query(db, qualified_name, version, tenant_id)
    if stored is None:
        raise QueryNotFoundError(qualified_name, version)

    params = parameters or {}
    handler = _QUERY_HANDLERS.get(stored.query_type)
    if handler is None:
        raise UnsupportedQueryTypeError(stored.query_type)

    results = handler(db, tenant_id, params)
    log_audit_event(
        "STORED_QUERY_EXECUTED", tenant_id,
        f"name={qualified_name} version={version} params={params}",
    )
    return {
        "queryName": qualified_name,
        "version": version,
        "parameters": params,
        "resultCount": len(results),
        "results": results,
    }


# =============================================================================
# Custom Exceptions
# =============================================================================

class QueryNotFoundError(Exception):
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        super().__init__(f"Stored query {name}/{version} not found")


class UnsupportedQueryTypeError(Exception):
    def __init__(self, query_type: str):
        self.query_type = query_type
        super().__init__(f"Unsupported query type: {query_type}")


# =============================================================================
# Billing Query Handlers
# =============================================================================

def _apply_date_filters(query, date_column, params: dict):
    """Apply optional date_from / date_to filters to a SQLAlchemy query."""
    date_from = params.get("date_from")
    date_to = params.get("date_to")
    if date_from:
        query = query.filter(date_column >= date_from)
    if date_to:
        query = query.filter(date_column <= date_to)
    return query


def _handle_diagnosis_codes(
    db: Session, tenant_id: str, params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract ICD-10 diagnosis codes from trade state transitions.

    Maps trade states to diagnostic categories:
    - New       -> Z00.00 (Encounter for general examination)
    - Processing -> Z01.89 (Encounter for other specified examinations)
    - Settled   -> Z09    (Encounter for follow-up after treatment)
    - Cancelled -> Z53.09 (Procedure not carried out)
    """
    STATE_TO_ICD10 = {
        "New": {"code": "Z00.00", "description": "Encounter for general examination"},
        "Processing": {"code": "Z01.89", "description": "Encounter for other specified examinations"},
        "Settled": {"code": "Z09", "description": "Encounter for follow-up after completed treatment"},
        "Cancelled": {"code": "Z53.09", "description": "Procedure and treatment not carried out"},
    }

    query = db.query(Trade).filter(Trade.tenant_id == tenant_id)
    query = _apply_date_filters(query, Trade.created, params)

    patient_id = params.get("patient_id")
    if patient_id is not None:
        query = query.filter(Trade.account_id == int(patient_id))

    results = []
    for trade in query.all():
        icd = STATE_TO_ICD10.get(trade.state, {
            "code": "R69", "description": "Illness, unspecified",
        })
        results.append({
            "diagnosisCode": icd["code"],
            "description": icd["description"],
            "category": "primary" if trade.state == "Settled" else "secondary",
            "dateOfDiagnosis": trade.created.isoformat() if trade.created else None,
            "clinicalContext": "inpatient" if trade.quantity >= 100 else "outpatient",
            "sourceTradeId": trade.id,
        })
    return results


def _handle_procedure_codes(
    db: Session, tenant_id: str, params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract CPT/HCPCS procedure codes from trade executions.

    Maps trade side/state to procedure codes:
    - Buy/Settled  -> 99213 (Office visit, established patient)
    - Sell/Settled -> 99214 (Office visit, detailed)
    - Buy/New      -> 99201 (Office visit, new patient, minimal)
    - Sell/New     -> 99202 (Office visit, new patient, low)
    """
    SIDE_STATE_TO_CPT = {
        ("Buy", "Settled"): {"code": "99213", "description": "Office visit, established patient"},
        ("Sell", "Settled"): {"code": "99214", "description": "Office visit, detailed"},
        ("Buy", "New"): {"code": "99201", "description": "Office visit, new patient, minimal"},
        ("Sell", "New"): {"code": "99202", "description": "Office visit, new patient, low"},
        ("Buy", "Processing"): {"code": "99211", "description": "Office visit, minimal"},
        ("Sell", "Processing"): {"code": "99215", "description": "Office visit, comprehensive"},
    }

    query = db.query(Trade).filter(Trade.tenant_id == tenant_id)
    query = _apply_date_filters(query, Trade.created, params)

    patient_id = params.get("patient_id")
    if patient_id is not None:
        query = query.filter(Trade.account_id == int(patient_id))

    results = []
    for trade in query.all():
        cpt = SIDE_STATE_TO_CPT.get((trade.side, trade.state), {
            "code": "99199", "description": "Unlisted special service or procedure",
        })
        results.append({
            "procedureCode": cpt["code"],
            "description": cpt["description"],
            "dateOfService": trade.created.isoformat() if trade.created else None,
            "performingProviderRef": f"provider-{trade.account_id}",
            "sourceTradeId": trade.id,
        })
    return results


def _handle_encounter_summary(
    db: Session, tenant_id: str, params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract encounter-level data from accounts and their trade activity."""
    query = db.query(Account).filter(Account.tenant_id == tenant_id)

    patient_id = params.get("patient_id")
    if patient_id is not None:
        query = query.filter(Account.id == int(patient_id))

    results = []
    for account in query.all():
        trades_q = db.query(Trade).filter(
            Trade.account_id == account.id,
            Trade.tenant_id == tenant_id,
        )
        trades_q = _apply_date_filters(trades_q, Trade.created, params)
        trades = trades_q.all()

        if not trades:
            continue

        first_trade = min(trades, key=lambda t: t.created or datetime.min)
        last_trade = max(trades, key=lambda t: t.updated or datetime.min)

        settled_count = sum(1 for t in trades if t.state == "Settled")
        encounter_type = "inpatient" if len(trades) >= 5 else "outpatient"

        results.append({
            "accountId": account.id,
            "accountName": account.display_name,
            "admissionDate": first_trade.created.isoformat() if first_trade.created else None,
            "dischargeDate": last_trade.updated.isoformat() if last_trade.updated else None,
            "encounterType": encounter_type,
            "attendingProvider": f"provider-{account.id}",
            "facilityId": f"facility-{tenant_id}",
            "totalProcedures": len(trades),
            "settledProcedures": settled_count,
        })
    return results


def _handle_patient_coverage(
    db: Session, tenant_id: str, params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract patient demographic and coverage data from account users."""
    query = db.query(AccountUser).filter(AccountUser.tenant_id == tenant_id)

    patient_id = params.get("patient_id")
    if patient_id is not None:
        query = query.filter(AccountUser.account_id == int(patient_id))

    results = []
    for user in query.all():
        account = db.query(Account).filter(
            Account.id == user.account_id,
            Account.tenant_id == tenant_id,
        ).first()

        position_count = db.query(func.count()).filter(
            Position.account_id == user.account_id,
            Position.tenant_id == tenant_id,
        ).scalar()

        results.append({
            "patientId": f"patient-{user.account_id}-{user.username}",
            "accountId": user.account_id,
            "username": user.username,
            "accountName": account.display_name if account else None,
            "insurancePlan": f"plan-{tenant_id}-standard",
            "subscriberId": f"sub-{user.account_id}",
            "coveragePeriodStart": None,
            "coveragePeriodEnd": None,
            "activePositions": position_count,
        })
    return results


# Handler dispatch table
_QUERY_HANDLERS: dict[str, Any] = {
    "diagnosis_codes": _handle_diagnosis_codes,
    "procedure_codes": _handle_procedure_codes,
    "encounter_summary": _handle_encounter_summary,
    "patient_coverage": _handle_patient_coverage,
}


# =============================================================================
# Seed Data — Pre-built billing queries
# =============================================================================

_COMMON_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "date_from": {
            "type": "string",
            "format": "date-time",
            "description": "Start of date range filter (ISO 8601)",
        },
        "date_to": {
            "type": "string",
            "format": "date-time",
            "description": "End of date range filter (ISO 8601)",
        },
        "patient_id": {
            "type": "integer",
            "description": "Account/patient ID filter",
        },
    },
}

BILLING_SEED_QUERIES = [
    {
        "qualified_name": "billing::diagnosis-codes",
        "version": "1.0.0",
        "description": (
            "Extracts ICD-10 diagnosis codes from trade state transitions. "
            "Returns primary and secondary diagnosis codes, date of diagnosis, "
            "and clinical context (inpatient/outpatient)."
        ),
        "query_type": "diagnosis_codes",
        "query_definition": {
            "fields": [
                "diagnosisCode", "description", "category",
                "dateOfDiagnosis", "clinicalContext", "sourceTradeId",
            ],
            "source": "trades",
            "mapping": "trade_state_to_icd10",
        },
        "parameters_schema": _COMMON_PARAMETERS_SCHEMA,
    },
    {
        "qualified_name": "billing::procedure-codes",
        "version": "1.0.0",
        "description": (
            "Extracts CPT/HCPCS procedure codes from trade executions. "
            "Returns procedure code with description, date of service, "
            "and performing provider reference."
        ),
        "query_type": "procedure_codes",
        "query_definition": {
            "fields": [
                "procedureCode", "description", "dateOfService",
                "performingProviderRef", "sourceTradeId",
            ],
            "source": "trades",
            "mapping": "trade_side_state_to_cpt",
        },
        "parameters_schema": _COMMON_PARAMETERS_SCHEMA,
    },
    {
        "qualified_name": "billing::encounter-summary",
        "version": "1.0.0",
        "description": (
            "Extracts encounter-level data needed for claims including "
            "admission/discharge dates, encounter type, attending provider, "
            "and facility information."
        ),
        "query_type": "encounter_summary",
        "query_definition": {
            "fields": [
                "accountId", "accountName", "admissionDate", "dischargeDate",
                "encounterType", "attendingProvider", "facilityId",
                "totalProcedures", "settledProcedures",
            ],
            "source": "accounts+trades",
            "mapping": "account_trade_activity_to_encounter",
        },
        "parameters_schema": _COMMON_PARAMETERS_SCHEMA,
    },
    {
        "qualified_name": "billing::patient-coverage",
        "version": "1.0.0",
        "description": (
            "Extracts patient demographic and coverage data including "
            "patient identifiers, insurance plan details, subscriber "
            "information, and coverage period."
        ),
        "query_type": "patient_coverage",
        "query_definition": {
            "fields": [
                "patientId", "accountId", "username", "accountName",
                "insurancePlan", "subscriberId", "coveragePeriodStart",
                "coveragePeriodEnd", "activePositions",
            ],
            "source": "account_users+accounts+positions",
            "mapping": "account_user_to_coverage",
        },
        "parameters_schema": _COMMON_PARAMETERS_SCHEMA,
    },
]


def seed_billing_queries(db: Session, tenant_id: str) -> list[StoredQuery]:
    """Register all pre-built billing queries for the given tenant."""
    registered = []
    for seed in BILLING_SEED_QUERIES:
        sq = register_query(
            db=db,
            qualified_name=seed["qualified_name"],
            version=seed["version"],
            query_type=seed["query_type"],
            query_definition=seed["query_definition"],
            tenant_id=tenant_id,
            description=seed["description"],
            parameters_schema=seed["parameters_schema"],
        )
        registered.append(sq)
    logger.info("Seeded %d billing queries for tenant %s",
                len(registered), tenant_id)
    return registered
