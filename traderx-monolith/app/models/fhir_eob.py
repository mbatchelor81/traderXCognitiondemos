"""
FHIR R4 ExplanationOfBenefit Pydantic models.
Defines the data structures for FHIR R4-compliant EOB resources
mapped from TraderX application data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# FHIR R4 Primitive / Shared Types
# =============================================================================

class FhirCoding(BaseModel):
    system: str
    code: str
    display: Optional[str] = None


class FhirCodeableConcept(BaseModel):
    coding: list[FhirCoding] = Field(default_factory=list)
    text: Optional[str] = None


class FhirReference(BaseModel):
    reference: str
    display: Optional[str] = None


class FhirPeriod(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class FhirMoney(BaseModel):
    value: float
    currency: str = "USD"


class FhirIdentifier(BaseModel):
    system: str
    value: str


# =============================================================================
# FHIR R4 EOB Sub-Resources
# =============================================================================

class EobItem(BaseModel):
    sequence: int
    productOrService: FhirCodeableConcept
    servicedDate: Optional[str] = None
    quantity: Optional[dict] = None
    unitPrice: Optional[FhirMoney] = None
    net: Optional[FhirMoney] = None
    adjudication: list[dict] = Field(default_factory=list)


class EobTotal(BaseModel):
    category: FhirCodeableConcept
    amount: FhirMoney


class EobInsurance(BaseModel):
    focal: bool = True
    coverage: FhirReference


class EobPayee(BaseModel):
    type: FhirCodeableConcept
    party: Optional[FhirReference] = None


# =============================================================================
# FHIR R4 ExplanationOfBenefit Resource
# =============================================================================

class ExplanationOfBenefit(BaseModel):
    resourceType: str = "ExplanationOfBenefit"
    id: str
    identifier: list[FhirIdentifier] = Field(default_factory=list)
    status: str = "active"
    type: FhirCodeableConcept
    use: str = "claim"
    patient: FhirReference
    billablePeriod: Optional[FhirPeriod] = None
    created: str
    insurer: FhirReference
    provider: FhirReference
    payee: Optional[EobPayee] = None
    outcome: str = "complete"
    insurance: list[EobInsurance] = Field(default_factory=list)
    item: list[EobItem] = Field(default_factory=list)
    total: list[EobTotal] = Field(default_factory=list)


# =============================================================================
# FHIR R4 Bundle (for paginated responses)
# =============================================================================

class FhirBundleLink(BaseModel):
    relation: str
    url: str


class FhirBundleEntry(BaseModel):
    fullUrl: str
    resource: ExplanationOfBenefit


class FhirBundle(BaseModel):
    resourceType: str = "Bundle"
    id: str
    type: str = "searchset"
    total: int
    link: list[FhirBundleLink] = Field(default_factory=list)
    entry: list[FhirBundleEntry] = Field(default_factory=list)
