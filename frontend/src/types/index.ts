export interface ProvenanceValue<T = any> {
  value: T;
  source: 'user_provided' | 'ai_inferred' | 'default' | 'confirmed';
  confidence: number;
}

export interface SpendingDistribution {
  food_groceries: number;
  online_shopping: number;
  travel: number;
  dining_entertainment: number;
  fuel: number;
  utility_bills: number;
  other: number;
}

export interface CardPreferences {
  low_annual_fee: boolean;
  cashback_priority: boolean;
  travel_perks: boolean;
  lounge_access: boolean;
  dining_discounts: boolean;
  fuel_surcharge_waiver: boolean;
  avoid_interest: boolean;
  existing_bank?: string | null;
}

export interface LoanPreferences {
  requested_amount?: number | null;
  requested_tenure_months?: number | null;
  max_affordable_emi?: number | null;
  purpose?: string | null;
  prefer_low_processing_fee: boolean;
  prefer_no_prepayment_penalty: boolean;
}

export interface FinancialProfile {
  monthly_income?: ProvenanceValue<number> | null;
  employment_type?: ProvenanceValue<string> | null;
  credit_score?: ProvenanceValue<number> | null;
  existing_monthly_emi?: ProvenanceValue<number> | null;
  city?: ProvenanceValue<string> | null;
  age?: ProvenanceValue<number> | null;
  preferred_product: 'credit_card' | 'personal_loan' | 'both';
  spending: SpendingDistribution;
  card_preferences: CardPreferences;
  loan_preferences: LoanPreferences;
  missing_information: string[];
  requires_confirmation: string[];
  is_complete: boolean;
}

export interface ClarificationQuestion {
  field: string;
  question: string;
  reason: string;
  options?: string[] | null;
}

export interface ProfileResponse {
  id: string;
  session_id?: string | null;
  profile: FinancialProfile;
  clarifications: ClarificationQuestion[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface FieldEvidence {
  id: string;
  field_name: string;
  extracted_value: any;
  normalized_value: any;
  evidence_excerpt: string;
  source_url: string;
  verification_status: 'verified' | 'partially_verified' | 'conflicting_sources' | 'stale' | 'unverified';
  confidence: number;
  verified_at: string;
}

export interface Product {
  id: string;
  product_name: string;
  issuer: string;
  product_type: 'credit_card' | 'personal_loan';
  canonical_url: string;
  structured_terms: Record<string, any>;
  data_quality_status: 'verified' | 'partially_verified' | 'conflicting_sources' | 'stale' | 'unverified';
  last_verified_at: string;
  active: boolean;
  field_evidences?: FieldEvidence[];
}

export interface ScoreBreakdown {
  eligibility: number;
  financial_suitability: number;
  preference_match: number;
  cost_efficiency: number;
  data_reliability: number;
  data_freshness: number;
}

export interface FinancialCalculations {
  requested_amount?: number;
  requested_tenure_months?: number;
  estimated_emi_min?: number;
  estimated_emi_max?: number;
  total_repayment_min?: number;
  total_repayment_max?: number;
  total_interest_min?: number;
  total_interest_max?: number;
  estimated_processing_fee?: number;
  emi_to_income_ratio?: number;
  is_zero_interest?: boolean;

  estimated_annual_spend?: number;
  estimated_annual_rewards?: number;
  annual_fee_effective?: number;
  fee_waived?: boolean;
  net_annual_benefit?: number;
  first_year_net_benefit?: number;
  reward_breakdown_by_category?: Record<string, number>;
}

export interface Explanation {
  why_it_matches: string;
  priority_fit: string;
  financial_impact: string;
  rank_reasoning?: string;
  drawbacks_and_tradeoffs: string[];
  eligibility_limitations: string;
  assumptions: string[];
  what_to_verify_before_applying: string[];
  official_sources: Array<{ title: string; url: string }>;
}

export interface RecommendationItem {
  id: string;
  product_id: string;
  product: Product;
  match_score: number;
  eligibility_status: 'meets_published_criteria' | 'may_meet_criteria' | 'does_not_meet_published_criteria';
  score_breakdown: ScoreBreakdown;
  financial_calculations: FinancialCalculations;
  explanation: Explanation;
  matched_preferences: string[];
  mismatches: string[];
  unknowns: string[];
  calculation_assumptions: string[];
}

export interface RecommendationRunResponse {
  run_id: string;
  profile_id: string;
  product_category: string;
  profile_summary: FinancialProfile;
  recommendations: RecommendationItem[];
  total_evaluated: number;
  created_at: string;
}

export interface ComparisonItem {
  product: Product;
  financial_calculations?: FinancialCalculations;
  pros: string[];
  cons: string[];
}

export interface ComparisonResponse {
  category: string;
  products: ComparisonItem[];
}
