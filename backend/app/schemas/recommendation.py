"""
Pydantic schemas for Recommendations, Explanations, and Product Comparisons.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from backend.app.schemas.product import ProductOut
from backend.app.schemas.profile import FinancialProfile


class ScoreBreakdown(BaseModel):
    eligibility: float = 0.0
    financial_suitability: float = 0.0
    preference_match: float = 0.0
    cost_efficiency: float = 0.0
    data_reliability: float = 0.0
    data_freshness: float = 0.0


class FinancialCalculations(BaseModel):
    # Loan specific metrics
    requested_amount: Optional[float] = None
    requested_tenure_months: Optional[int] = None
    estimated_emi_min: Optional[float] = None
    estimated_emi_max: Optional[float] = None
    total_repayment_min: Optional[float] = None
    total_repayment_max: Optional[float] = None
    total_interest_min: Optional[float] = None
    total_interest_max: Optional[float] = None
    estimated_processing_fee: Optional[float] = None
    emi_to_income_ratio: Optional[float] = None
    is_zero_interest: bool = False

    # Credit card specific metrics
    estimated_annual_spend: Optional[float] = None
    estimated_annual_rewards: Optional[float] = None
    annual_fee_effective: Optional[float] = None
    fee_waived: bool = False
    net_annual_benefit: Optional[float] = None
    reward_breakdown_by_category: Dict[str, float] = Field(default_factory=dict)
    first_year_net_benefit: Optional[float] = None


class ExplanationOut(BaseModel):
    why_it_matches: str
    priority_fit: str
    financial_impact: str
    rank_reasoning: Optional[str] = None
    drawbacks_and_tradeoffs: List[str] = Field(default_factory=list)
    eligibility_limitations: str
    assumptions: List[str] = Field(default_factory=list)
    what_to_verify_before_applying: List[str] = Field(default_factory=list)
    official_sources: List[Dict[str, str]] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    id: str
    product_id: str
    product: ProductOut
    match_score: float
    eligibility_status: Literal["meets_published_criteria", "may_meet_criteria", "does_not_meet_published_criteria"]
    score_breakdown: ScoreBreakdown
    financial_calculations: FinancialCalculations
    explanation: ExplanationOut
    matched_preferences: List[str] = Field(default_factory=list)
    mismatches: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    calculation_assumptions: List[str] = Field(default_factory=list)


class RecommendationRunResponse(BaseModel):
    run_id: str
    profile_id: str
    product_category: str
    profile_summary: FinancialProfile
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    total_evaluated: int = 0
    created_at: str


class ComparisonRequest(BaseModel):
    product_ids: List[str] = Field(..., min_length=2, max_length=4)
    profile_id: Optional[str] = None


class ComparisonItem(BaseModel):
    product: ProductOut
    financial_calculations: Optional[FinancialCalculations] = None
    match_score: Optional[float] = None
    eligibility_status: Optional[str] = None
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class ComparisonResponse(BaseModel):
    category: str
    products: List[ComparisonItem]
    common_attributes: Dict[str, Any] = Field(default_factory=dict)
