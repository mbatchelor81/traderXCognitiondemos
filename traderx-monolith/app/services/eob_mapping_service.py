"""
FHIR R4 ExplanationOfBenefit mapping service.
Transforms TraderX application data (trades, accounts, positions)
into FHIR R4 ExplanationOfBenefit resources.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.config import *  # noqa: F401,F403 — intentional global config import
from app.models.account import Account
from app.models.fhir_eob import (
    EobInsurance,
    EobItem,
    EobPayee,
    EobTotal,
    ExplanationOfBenefit,
    FhirBundle,
    FhirBundleEntry,
    FhirBundleLink,
    FhirCodeableConcept,
    FhirCoding,
    FhirIdentifier,
    FhirMoney,
    FhirPeriod,
    FhirReference,
)
from app.models.trade import Trade
from app.utils.helpers import format_datetime

logger = logging.getLogger(__name__)

FHIR_EOB_SYSTEM = "http://terminology.hl7.org/CodeSystem/claim-type"
TRADERX_SYSTEM = "https://traderx.example.com/fhir"

_TRADE_STATE_TO_EOB_STATUS: dict[str, str] = {
    "New": "active",
    "Processing": "active",
    "Settled": "active",
    "Cancelled": "cancelled",
}

_TRADE_STATE_TO_EOB_OUTCOME: dict[str, str] = {
    "New": "queued",
    "Processing": "queued",
    "Settled": "complete",
    "Cancelled": "error",
}


# =============================================================================
# Trade → EOB Mapping
# =============================================================================

def map_trade_to_eob(trade: Trade, account: Account) -> ExplanationOfBenefit:
    """Map a single Trade record to a FHIR R4 ExplanationOfBenefit resource."""
    eob_id = f"eob-trade-{trade.id}"
    created = format_datetime(trade.created) or ""

    item = EobItem(
        sequence=1,
        productOrService=FhirCodeableConcept(
            coding=[FhirCoding(
                system=f"{TRADERX_SYSTEM}/security",
                code=trade.security,
                display=f"{trade.security} ({trade.side})",
            )],
            text=f"{trade.side} {trade.quantity} x {trade.security}",
        ),
        servicedDate=format_datetime(trade.created),
        quantity={"value": trade.quantity, "unit": "shares"},
    )

    eob_type = FhirCodeableConcept(
        coding=[FhirCoding(
            system=FHIR_EOB_SYSTEM,
            code="professional",
            display="Professional",
        )],
        text="Trade Settlement",
    )

    total_category = FhirCodeableConcept(
        coding=[FhirCoding(
            system="http://terminology.hl7.org/CodeSystem/adjudication",
            code="submitted",
            display="Submitted Amount",
        )],
    )

    return ExplanationOfBenefit(
        id=eob_id,
        identifier=[FhirIdentifier(
            system=f"{TRADERX_SYSTEM}/trade-id",
            value=str(trade.id),
        )],
        status=_TRADE_STATE_TO_EOB_STATUS.get(trade.state, "active"),
        type=eob_type,
        use="claim",
        patient=FhirReference(
            reference=f"Patient/{trade.account_id}",
            display=account.display_name or f"Account {trade.account_id}",
        ),
        billablePeriod=FhirPeriod(
            start=format_datetime(trade.created),
            end=format_datetime(trade.updated),
        ),
        created=created,
        insurer=FhirReference(
            reference=f"Organization/{trade.tenant_id}",
            display=trade.tenant_id,
        ),
        provider=FhirReference(
            reference="Organization/traderx",
            display="TraderX Platform",
        ),
        payee=EobPayee(
            type=FhirCodeableConcept(
                coding=[FhirCoding(
                    system="http://terminology.hl7.org/CodeSystem/payeetype",
                    code="subscriber",
                    display="Subscriber",
                )],
            ),
            party=FhirReference(
                reference=f"Patient/{trade.account_id}",
                display=account.display_name or f"Account {trade.account_id}",
            ),
        ),
        outcome=_TRADE_STATE_TO_EOB_OUTCOME.get(trade.state, "queued"),
        insurance=[EobInsurance(
            focal=True,
            coverage=FhirReference(
                reference=f"Coverage/{trade.tenant_id}-{trade.account_id}",
                display=f"{trade.tenant_id} coverage",
            ),
        )],
        item=[item],
        total=[EobTotal(
            category=total_category,
            amount=FhirMoney(value=float(trade.quantity), currency="USD"),
        )],
    )


# =============================================================================
# Query + Bundle
# =============================================================================

def get_eobs_for_patient(
    db: Session,
    patient_id: int,
    tenant_id: str,
    base_url: str,
    offset: int = 0,
    count: int = 10,
) -> Optional[FhirBundle]:
    """
    Query trades for the given patient (account_id) and tenant,
    then return a paginated FHIR Bundle of EOB resources.
    Returns None if the account does not exist or doesn't belong to the tenant.
    """
    account = db.query(Account).filter(
        Account.id == patient_id,
        Account.tenant_id == tenant_id,
    ).first()

    if account is None:
        return None

    total_count = db.query(Trade).filter(
        Trade.account_id == patient_id,
        Trade.tenant_id == tenant_id,
    ).count()

    trades = (
        db.query(Trade)
        .filter(
            Trade.account_id == patient_id,
            Trade.tenant_id == tenant_id,
        )
        .order_by(Trade.created.desc())
        .offset(offset)
        .limit(count)
        .all()
    )

    entries = [
        FhirBundleEntry(
            fullUrl=f"{base_url}/fhir/r4/ExplanationOfBenefit/{eob.id}",
            resource=eob,
        )
        for trade in trades
        if (eob := map_trade_to_eob(trade, account)) is not None
    ]

    links: list[FhirBundleLink] = [
        FhirBundleLink(
            relation="self",
            url=f"{base_url}/fhir/r4/ExplanationOfBenefit"
                f"?patient={patient_id}&_offset={offset}&_count={count}",
        ),
    ]

    if offset + count < total_count:
        links.append(FhirBundleLink(
            relation="next",
            url=f"{base_url}/fhir/r4/ExplanationOfBenefit"
                f"?patient={patient_id}&_offset={offset + count}&_count={count}",
        ))

    bundle_id = str(uuid.uuid4())

    return FhirBundle(
        id=bundle_id,
        type="searchset",
        total=total_count,
        link=links,
        entry=entries,
    )
