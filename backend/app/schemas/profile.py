"""
Pydantic schemas for User Profile and Conversational Interactions.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class ProvenanceValue(BaseModel):
    value: Any = None
    source: Literal["user_provided", "ai_inferred", "default", "confirmed"] = "user_provided"
    confidence: float = 1.0


class SpendingDistribution(BaseModel):
    food_groceries: float = 0.0
    online_shopping: float = 0.0
    travel: float = 0.0
    dining_entertainment: float = 0.0
    fuel: float = 0.0
    utility_bills: float = 0.0
    other: float = 0.0

    @property
    def total_monthly_spend(self) -> float:
        return (
            self.food_groceries
            + self.online_shopping
            + self.travel
            + self.dining_entertainment
            + self.fuel
            + self.utility_bills
            + self.other
        )


class CardPreferences(BaseModel):
    low_annual_fee: bool = False
    cashback_priority: bool = False
    travel_perks: bool = False
    lounge_access: bool = False
    dining_discounts: bool = False
    fuel_surcharge_waiver: bool = False
    avoid_interest: bool = True  # Pay full every month
    existing_bank: Optional[str] = None  # e.g., "HDFC", "SBI"


class LoanPreferences(BaseModel):
    requested_amount: Optional[float] = None
    requested_tenure_months: Optional[int] = None
    max_affordable_emi: Optional[float] = None
    purpose: Optional[str] = None  # e.g., "debt_consolidation", "home_renovation", "medical", "wedding"
    prefer_low_processing_fee: bool = True
    prefer_no_prepayment_penalty: bool = True


class FinancialProfile(BaseModel):
    # Core demographic & financial
    monthly_income: Optional[ProvenanceValue] = None
    employment_type: Optional[ProvenanceValue] = None  # "salaried", "self_employed", "business", "student", "retired"
    credit_score: Optional[ProvenanceValue] = None  # 300 - 900
    existing_monthly_emi: Optional[ProvenanceValue] = None
    city: Optional[ProvenanceValue] = None
    age: Optional[ProvenanceValue] = None

    # Preferred product category: "credit_card", "personal_loan", or "both"
    preferred_product: Literal["credit_card", "personal_loan", "both"] = "credit_card"

    # Specific preference blocks
    spending: SpendingDistribution = Field(default_factory=SpendingDistribution)
    card_preferences: CardPreferences = Field(default_factory=CardPreferences)
    loan_preferences: LoanPreferences = Field(default_factory=LoanPreferences)

    # State tracking
    missing_information: List[str] = Field(default_factory=list)
    requires_confirmation: List[str] = Field(default_factory=list)
    is_complete: bool = False


class ClarificationQuestion(BaseModel):
    field: str
    question: str
    reason: str
    options: Optional[List[str]] = None  # Compact selectable suggestions


class ClarificationResponse(BaseModel):
    profile_complete: bool
    questions: List[ClarificationQuestion] = Field(default_factory=list)


# API Request / Response schemas
class ProfileParseRequest(BaseModel):
    message: str
    category: Optional[Literal["credit_card", "personal_loan", "both"]] = None
    session_id: Optional[str] = None


class ProfileChatRequest(BaseModel):
    profile_id: str
    message: str


class ProfileUpdateRequest(BaseModel):
    monthly_income: Optional[float] = None
    employment_type: Optional[str] = None
    credit_score: Optional[int] = None
    existing_monthly_emi: Optional[float] = None
    city: Optional[str] = None
    age: Optional[int] = None
    preferred_product: Optional[Literal["credit_card", "personal_loan", "both"]] = None
    spending: Optional[Dict[str, float]] = None
    card_preferences: Optional[Dict[str, Any]] = None
    loan_preferences: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    profile: FinancialProfile
    clarifications: List[ClarificationQuestion] = Field(default_factory=list)
    version: int
    created_at: str
    updated_at: str
