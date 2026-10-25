"""
Deterministic Matching and Ranking Engine:
Computes reproducible 0-100 scores across 6 transparent dimensions:
- Eligibility compatibility (30%)
- Financial suitability (25%)
- Preference match (20%)
- Cost efficiency (15%)
- Data reliability (5%)
- Data freshness (5%)
With stable tie-breaking rules and full financial calculation attachments.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas.profile import FinancialProfile
from backend.app.schemas.product import CreditCardTerms, LoanTerms
from backend.app.schemas.recommendation import ScoreBreakdown, FinancialCalculations
from backend.app.services.eligibility_engine import EligibilityEngine
from backend.app.services.loan_calculator import calculate_loan_range_metrics
from backend.app.services.card_value_calculator import calculate_credit_card_annual_value


class MatchingEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Configurable weights summing to 1.0
        self.weights = weights or {
            "eligibility": 0.30,
            "financial_suitability": 0.25,
            "preference_match": 0.20,
            "cost_efficiency": 0.15,
            "data_reliability": 0.05,
            "data_freshness": 0.05,
        }
        self.eligibility_engine = EligibilityEngine()

    def evaluate_and_rank_products(
        self,
        profile: FinancialProfile,
        products: List[Dict[str, Any]],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a list of products against the user profile and ranks them in deterministic order.
        """
        results = []
        for p in products:
            p_type = p.get("product_type", "credit_card")
            if category and category != "both" and p_type != category:
                continue

            scored_item = self._score_product(profile, p)
            results.append(scored_item)

        # Deterministic Stable Sorting:
        # 1. Match score descending
        # 2. Eligibility status priority: meets_published_criteria > may_meet_criteria > does_not_meet
        # 3. Product name ascending (for identical ties)
        status_priority = {
            "meets_published_criteria": 3,
            "may_meet_criteria": 2,
            "does_not_meet_published_criteria": 1
        }
        results.sort(
            key=lambda x: (
                round(x["match_score"], 1),
                status_priority.get(x["eligibility_status"], 0),
                -1 * (x.get("financial_calculations", {}).get("net_annual_benefit") or 0.0),
                x["product"].get("product_name", "")
            ),
            reverse=True
        )

        return results

    def _score_product(self, profile: FinancialProfile, product: Dict[str, Any]) -> Dict[str, Any]:
        p_type = product.get("product_type", "credit_card")
        terms_dict = product.get("structured_terms") or product.get("terms") or {}
        quality_status = product.get("data_quality_status", "verified")
        last_verified = product.get("last_verified_at")

        # 1. Eligibility Evaluation
        elig_res = self.eligibility_engine.evaluate(profile, terms_dict)
        elig_score = elig_res.score

        # 2. Data Reliability & Freshness Scores
        rel_score = {"verified": 100.0, "partially_verified": 70.0, "conflicting_sources": 30.0, "stale": 40.0}.get(quality_status, 20.0)
        fresh_score = 100.0
        if last_verified:
            try:
                dt = datetime.fromisoformat(str(last_verified).replace("Z", "+00:00"))
                days_old = (datetime.now(timezone.utc) - dt).days
                if days_old <= 7:
                    fresh_score = 100.0
                elif days_old <= 30:
                    fresh_score = 85.0
                else:
                    fresh_score = 50.0
            except Exception:
                fresh_score = 80.0

        matched_prefs: List[str] = []
        mismatches: List[str] = []
        assumptions: List[str] = []
        fin_calc_dict: Dict[str, Any] = {}

        if p_type == "credit_card":
            fin_score, pref_score, cost_score, fin_calc_dict, matched_prefs, mismatches, assumptions = (
                self._evaluate_credit_card(profile, terms_dict, product)
            )
        else:
            fin_score, pref_score, cost_score, fin_calc_dict, matched_prefs, mismatches, assumptions = (
                self._evaluate_loan(profile, terms_dict, product)
            )

        # Calculate weighted composite match score
        total_score = (
            self.weights["eligibility"] * elig_score
            + self.weights["financial_suitability"] * fin_score
            + self.weights["preference_match"] * pref_score
            + self.weights["cost_efficiency"] * cost_score
            + self.weights["data_reliability"] * rel_score
            + self.weights["data_freshness"] * fresh_score
        )
        total_score = round(max(0.0, min(100.0, total_score)), 1)

        breakdown = ScoreBreakdown(
            eligibility=round(elig_score, 1),
            financial_suitability=round(fin_score, 1),
            preference_match=round(pref_score, 1),
            cost_efficiency=round(cost_score, 1),
            data_reliability=round(rel_score, 1),
            data_freshness=round(fresh_score, 1),
        )

        return {
            "product_id": product.get("id", ""),
            "product": product,
            "match_score": total_score,
            "eligibility_status": elig_res.status,
            "score_breakdown": breakdown.model_dump(),
            "financial_calculations": fin_calc_dict,
            "matched_preferences": matched_prefs,
            "mismatches": mismatches,
            "unknowns": elig_res.unknown_criteria,
            "calculation_assumptions": assumptions,
        }

    def _evaluate_credit_card(
        self,
        profile: FinancialProfile,
        terms_dict: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Tuple[float, float, float, Dict[str, Any], List[str], List[str], List[str]]:
        terms = CreditCardTerms(**terms_dict)
        spending = profile.spending
        card_val = calculate_credit_card_annual_value(terms, spending)

        # Financial suitability: Reward yield and net benefit relative to spend
        annual_spend = card_val["estimated_annual_spend"]
        net_benefit = card_val["net_annual_benefit"]
        if annual_spend > 0:
            yield_pct = (net_benefit / annual_spend) * 100.0
            # 3% net yield translates to ~90 score
            fin_score = min(100.0, max(20.0, yield_pct * 30.0))
        else:
            fin_score = 65.0  # Spend unstated

        # Preference Match
        pref_score = 70.0
        matched_prefs: List[str] = []
        mismatches: List[str] = []
        
        # Fee preference
        if profile.card_preferences.low_annual_fee:
            if terms.annual_fee == 0 or card_val["fee_waived"]:
                pref_score += 15.0
                matched_prefs.append("Aligns with preference for zero / low annual fee.")
            elif terms.annual_fee <= 500:
                pref_score += 5.0
                matched_prefs.append("Modest annual fee within low fee tolerance.")
            else:
                pref_score -= 20.0
                mismatches.append(f"Higher annual fee of ₹{terms.annual_fee:,.0f} exceeds low-fee preference.")

        # Cashback preference
        if profile.card_preferences.cashback_priority:
            if (terms.online_shopping_cashback_pct or 0) >= 3.0 or (terms.grocery_cashback_pct or 0) >= 3.0:
                pref_score += 15.0
                matched_prefs.append("High cashback rate on primary spending categories.")

        # Existing bank relationship
        user_bank = profile.card_preferences.existing_bank
        issuer = product.get("issuer", "").upper()
        if user_bank and (user_bank in issuer or issuer in user_bank):
            pref_score += 10.0
            matched_prefs.append(f"Existing banking relationship with {issuer} simplifies processing.")

        pref_score = min(100.0, max(10.0, pref_score))

        # Cost Efficiency
        if terms.annual_fee == 0:
            cost_score = 100.0
        elif card_val["fee_waived"]:
            cost_score = 90.0
        elif terms.annual_fee <= 500:
            cost_score = 75.0
        elif terms.annual_fee <= 1000:
            cost_score = 60.0
        else:
            cost_score = 40.0

        fin_calc = {
            "estimated_annual_spend": annual_spend,
            "estimated_annual_rewards": card_val["estimated_annual_rewards"],
            "annual_fee_effective": card_val["annual_fee_effective"],
            "fee_waived": card_val["fee_waived"],
            "net_annual_benefit": net_benefit,
            "first_year_net_benefit": card_val["first_year_net_benefit"],
            "reward_breakdown_by_category": card_val["reward_breakdown_by_category"]
        }

        return fin_score, pref_score, cost_score, fin_calc, matched_prefs, mismatches, card_val["assumptions"]

    def _evaluate_loan(
        self,
        profile: FinancialProfile,
        terms_dict: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Tuple[float, float, float, Dict[str, Any], List[str], List[str], List[str]]:
        terms = LoanTerms(**terms_dict)
        req_amount = profile.loan_preferences.requested_amount or 300000.0
        req_tenure = profile.loan_preferences.requested_tenure_months or 36
        income = profile.monthly_income.value if profile.monthly_income else None
        curr_emi = profile.existing_monthly_emi.value if profile.existing_monthly_emi else 0.0

        range_metrics = calculate_loan_range_metrics(
            principal=req_amount,
            interest_rate_min=terms.interest_rate_min,
            interest_rate_max=terms.interest_rate_max,
            tenure_months=req_tenure,
            processing_fee_pct=terms.processing_fee_pct,
            min_processing_fee=terms.processing_fee_min,
            max_processing_fee=terms.processing_fee_max,
            monthly_income=income,
            existing_emi=curr_emi
        )

        matched_prefs: List[str] = []
        mismatches: List[str] = []

        # Financial suitability: does requested amount & tenure fall in allowed range?
        fin_score = 80.0
        if req_amount < terms.min_amount or req_amount > terms.max_amount:
            fin_score -= 40.0
            mismatches.append(f"Requested amount (₹{req_amount:,.0f}) is outside lender's limit (₹{terms.min_amount:,.0f} - ₹{terms.max_amount:,.0f}).")
        else:
            matched_prefs.append(f"Accommodates desired loan amount of ₹{req_amount:,.0f}.")

        if req_tenure < terms.min_tenure_months or req_tenure > terms.max_tenure_months:
            fin_score -= 20.0
            mismatches.append(f"Requested tenure ({req_tenure} mos) outside limits ({terms.min_tenure_months}-{terms.max_tenure_months} mos).")
        else:
            matched_prefs.append(f"Supports preferred repayment tenure of {req_tenure} months.")

        # Affordability / FOIR fit
        foir_max = range_metrics.get("foir_max_pct")
        if foir_max is not None:
            if foir_max <= 40.0:
                fin_score += 15.0
                matched_prefs.append(f"Estimated EMI is well within safe affordability guidelines (FOIR: {foir_max:.1f}%).")
            elif foir_max > 60.0:
                fin_score -= 25.0
                mismatches.append(f"High debt-to-income ratio ({foir_max:.1f}% FOIR) may impact lender approval.")

        fin_score = min(100.0, max(10.0, fin_score))

        # Preference match
        pref_score = 75.0
        if profile.loan_preferences.prefer_low_processing_fee:
            if terms.processing_fee_pct <= 1.5:
                pref_score += 15.0
                matched_prefs.append(f"Competitive processing fee of {terms.processing_fee_pct:.1f}%.")
            else:
                pref_score -= 10.0
                mismatches.append(f"Processing fee of {terms.processing_fee_pct:.1f}% is relatively high.")

        pref_score = min(100.0, max(10.0, pref_score))

        # Cost efficiency: based on interest rate competitiveness
        # Lowest rate ~ 10.5% gives ~90-100 score, 20% gives ~50
        cost_score = max(30.0, min(100.0, 100.0 - (terms.interest_rate_min - 9.0) * 5.0))

        fin_calc = {
            "requested_amount": req_amount,
            "requested_tenure_months": req_tenure,
            "estimated_emi_min": range_metrics["estimated_emi_min"],
            "estimated_emi_max": range_metrics["estimated_emi_max"],
            "total_repayment_min": range_metrics["total_repayment_min"],
            "total_repayment_max": range_metrics["total_repayment_max"],
            "total_interest_min": range_metrics["total_interest_min"],
            "total_interest_max": range_metrics["total_interest_max"],
            "estimated_processing_fee": range_metrics["estimated_processing_fee"],
            "is_zero_interest": range_metrics["is_zero_interest"],
            "emi_to_income_ratio": range_metrics.get("foir_min_pct"),
        }

        return fin_score, pref_score, cost_score, fin_calc, matched_prefs, mismatches, range_metrics["assumptions"]
