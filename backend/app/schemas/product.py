"""
Pydantic schemas for Products, Financial Terms, and Ingestion.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class CreditCardTerms(BaseModel):
    joining_fee: float = 0.0
    annual_fee: float = 0.0
    fee_waiver_spend_threshold: Optional[float] = None  # e.g. 100000/yr
    
    # Cashback / rewards structure
    base_cashback_pct: float = 1.0  # e.g. 1%
    grocery_cashback_pct: Optional[float] = None  # e.g. 5%
    online_shopping_cashback_pct: Optional[float] = None
    travel_cashback_pct: Optional[float] = None
    dining_cashback_pct: Optional[float] = None
    fuel_surcharge_waiver_pct: Optional[float] = None  # usually 1%
    
    monthly_reward_cap: Optional[float] = None  # in INR
    welcome_bonus_value: Optional[float] = None  # in INR
    lounge_visits_per_quarter: int = 0
    interest_rate_monthly_pct: float = 3.5  # standard Indian card ~3.5% pm (~42% pa)
    
    # Eligibility requirements published
    min_monthly_income: Optional[float] = None
    min_age: Optional[int] = 21
    max_age: Optional[int] = 65
    min_credit_score: Optional[int] = None
    salaried_only: bool = False

    perks: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    official_apply_url: Optional[str] = None


class LoanTerms(BaseModel):
    min_amount: float = 25000.0
    max_amount: float = 4000000.0
    interest_rate_min: float = 10.5  # Annual nominal rate %
    interest_rate_max: float = 24.0
    apr_min: Optional[float] = None
    apr_max: Optional[float] = None
    rate_type: Literal["reducing_balance", "flat", "floating", "fixed"] = "reducing_balance"
    
    min_tenure_months: int = 12
    max_tenure_months: int = 60
    
    processing_fee_pct: float = 1.5  # % of loan amount
    processing_fee_min: Optional[float] = 1000.0
    processing_fee_max: Optional[float] = 15000.0
    prepayment_charges_pct: Optional[float] = None
    foreclosure_charges_pct: Optional[float] = None
    
    # Eligibility requirements published
    min_monthly_income: Optional[float] = None
    min_age: Optional[int] = 21
    max_age: Optional[int] = 60
    min_credit_score: Optional[int] = None
    min_work_experience_years: Optional[float] = None

    perks: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    official_apply_url: Optional[str] = None


class FieldEvidenceOut(BaseModel):
    id: str
    field_name: str
    extracted_value: Any
    normalized_value: Any
    evidence_excerpt: str
    source_url: str
    verification_status: Literal["verified", "partially_verified", "conflicting_sources", "stale", "unverified"]
    confidence: float
    verified_at: str


class ProductOut(BaseModel):
    id: str
    product_name: str
    issuer: str
    product_type: Literal["credit_card", "personal_loan"]
    canonical_url: str
    structured_terms: Dict[str, Any]
    data_quality_status: Literal["verified", "partially_verified", "conflicting_sources", "stale", "unverified"]
    last_verified_at: str
    active: bool
    field_evidences: Optional[List[FieldEvidenceOut]] = None


class ProductFilterParams(BaseModel):
    product_type: Optional[Literal["credit_card", "personal_loan"]] = None
    issuer: Optional[str] = None
    max_fee: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    min_cashback: Optional[float] = None
    verification_status: Optional[str] = None
    search: Optional[str] = None
