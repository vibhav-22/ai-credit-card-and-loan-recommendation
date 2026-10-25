"""
Deterministic Eligibility Engine:
Compares structured user financial profile against published product requirements.
Uses three explicit outcomes:
- meets_published_criteria
- may_meet_criteria
- does_not_meet_published_criteria
Never fabricates unpublished criteria.
"""
from typing import Dict, Any, List, Tuple
from backend.app.schemas.profile import FinancialProfile


class EligibilityResult:
    def __init__(
        self,
        status: str,
        score: float,
        matched_criteria: List[str],
        mismatched_criteria: List[str],
        unknown_criteria: List[str]
    ):
        self.status = status
        self.score = score
        self.matched_criteria = matched_criteria
        self.mismatched_criteria = mismatched_criteria
        self.unknown_criteria = unknown_criteria

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "matched_criteria": self.matched_criteria,
            "mismatched_criteria": self.mismatched_criteria,
            "unknown_criteria": self.unknown_criteria
        }


class EligibilityEngine:
    def evaluate(self, profile: FinancialProfile, product_terms: Dict[str, Any]) -> EligibilityResult:
        matched: List[str] = []
        mismatched: List[str] = []
        unknowns: List[str] = []

        # 1. Income Requirement
        min_income = product_terms.get("min_monthly_income")
        user_income = profile.monthly_income.value if (profile.monthly_income and profile.monthly_income.value) else None

        if min_income is not None and min_income > 0:
            if user_income is not None:
                if user_income >= min_income:
                    matched.append(f"Monthly income (₹{user_income:,.0f}) meets published minimum (₹{min_income:,.0f}).")
                else:
                    mismatched.append(f"Monthly income (₹{user_income:,.0f}) is below published minimum (₹{min_income:,.0f}).")
            else:
                unknowns.append(f"Published minimum income is ₹{min_income:,.0f}, but your income was not specified.")
        else:
            unknowns.append("Issuer has not published an explicit minimum monthly income threshold.")

        # 2. Age Requirement
        min_age = product_terms.get("min_age", 21)
        max_age = product_terms.get("max_age", 65)
        user_age = profile.age.value if (profile.age and profile.age.value) else None

        if user_age is not None:
            if min_age <= user_age <= max_age:
                matched.append(f"Age ({user_age} yrs) is within published bracket ({min_age}-{max_age} yrs).")
            else:
                mismatched.append(f"Age ({user_age} yrs) falls outside published bracket ({min_age}-{max_age} yrs).")

        # 3. Credit Score Guidance
        min_score = product_terms.get("min_credit_score")
        user_score = profile.credit_score.value if (profile.credit_score and profile.credit_score.value) else None

        if min_score is not None and min_score > 0:
            if user_score is not None:
                if user_score >= min_score:
                    matched.append(f"Credit score ({user_score}) meets guidance threshold ({min_score}+).")
                else:
                    mismatched.append(f"Credit score ({user_score}) is below recommended guidance ({min_score}+).")
            else:
                unknowns.append(f"Recommended credit score is {min_score}+, but your score is unknown.")
        else:
            unknowns.append("No explicit credit score threshold is published by the institution.")

        # 4. Employment Type check for loans / cards
        salaried_only = product_terms.get("salaried_only", False)
        emp_type = profile.employment_type.value if profile.employment_type else None
        if salaried_only and emp_type and emp_type != "salaried":
            mismatched.append(f"Product is exclusively for salaried applicants; you indicated '{emp_type}'.")

        # Determine overall status and score (0 to 100)
        if mismatched:
            status = "does_not_meet_published_criteria"
            score = 20.0 if not any("below published minimum" in m for m in mismatched) else 0.0
        elif len(matched) >= 2:
            status = "meets_published_criteria"
            score = 100.0
        elif len(matched) >= 1:
            status = "may_meet_criteria"
            score = 80.0
        else:
            status = "may_meet_criteria"
            score = 60.0

        return EligibilityResult(
            status=status,
            score=score,
            matched_criteria=matched,
            mismatched_criteria=mismatched,
            unknown_criteria=unknowns
        )
