"""
LLM Recommendation Explainer:
Generates grounded, personalized explanations for recommendations without hallucinating
numbers, changing scores, or altering eligibility conclusions.
"""
from typing import Dict, Any, List
from backend.app.schemas.profile import FinancialProfile
from backend.app.schemas.recommendation import ExplanationOut
from backend.app.services.llm_provider import get_llm_provider
from backend.app.core.logging import logger


class RecommendationExplainer:
    def __init__(self):
        self.llm = get_llm_provider()

    async def explain_recommendation(
        self,
        profile: FinancialProfile,
        product: Dict[str, Any],
        scored_data: Dict[str, Any]
    ) -> ExplanationOut:
        """
        Produces grounded ExplanationOut conforming strictly to verified facts and calculations.
        """
        p_name = product.get("product_name", "Product")
        issuer = product.get("issuer", "Lender")
        p_type = product.get("product_type", "credit_card")
        canonical_url = product.get("canonical_url", "")
        fin_calc = scored_data.get("financial_calculations", {})
        status = scored_data.get("eligibility_status", "may_meet_criteria")
        matched = scored_data.get("matched_preferences", [])
        mismatches = scored_data.get("mismatches", [])
        assumptions = scored_data.get("calculation_assumptions", [])

        # Construct safe prompt
        prompt = (
            f"Generate personalized recommendation explanation for {p_name} by {issuer}.\n"
            f"User profile preferences: {profile.model_dump_json()}\n"
            f"Financial calculations: {fin_calc}\n"
            f"Eligibility status: {status}\n"
            f"Matched priorities: {matched}\n"
            f"Trade-offs / mismatches: {mismatches}\n"
            f"Assumptions: {assumptions}\n"
        )
        system_prompt = (
            "You are an expert, objective fintech recommendation explainer. "
            "Explain why this product fits the user's situation. Do NOT hallucinate fees, rates, "
            "or guarantee approvals. Return strictly structured JSON matching the Explanation schema."
        )

        try:
            raw_json = await self.llm.generate_json(prompt=prompt, system_prompt=system_prompt)
            # Ensure official_sources is always populated with the actual canonical source
            if not raw_json.get("official_sources"):
                raw_json["official_sources"] = [{"title": f"Official {issuer} Terms", "url": canonical_url}]
            return ExplanationOut(**raw_json)
        except Exception as e:
            logger.warning(f"LLM explainer error, falling back to deterministic explanation: {e}")
            return self._build_deterministic_explanation(
                profile, product, scored_data, fin_calc, status, matched, mismatches, assumptions, canonical_url
            )

    def _build_deterministic_explanation(
        self,
        profile: FinancialProfile,
        product: Dict[str, Any],
        scored_data: Dict[str, Any],
        fin_calc: Dict[str, Any],
        status: str,
        matched: List[str],
        mismatches: List[str],
        assumptions: List[str],
        canonical_url: str
    ) -> ExplanationOut:
        p_name = product.get("product_name", "Product")
        issuer = product.get("issuer", "Lender")
        p_type = product.get("product_type", "credit_card")

        if p_type == "credit_card":
            net_b = fin_calc.get("net_annual_benefit", 0.0)
            why_it_matches = (
                f"{p_name} ranks favorably for you because its verified cashback structure and fee terms "
                f"align with your spending distribution, producing an estimated net annual reward of ₹{net_b:,.0f}."
            )
            fin_impact = (
                f"Based on your stated monthly spend, you earn an estimated ₹{fin_calc.get('estimated_annual_rewards', 0.0):,.0f} "
                f"in annual rewards against an effective annual fee of ₹{fin_calc.get('annual_fee_effective', 0.0):,.0f}."
            )
        else:
            emi_min = fin_calc.get("estimated_emi_min", 0.0)
            emi_max = fin_calc.get("estimated_emi_max", 0.0)
            why_it_matches = (
                f"{p_name} matches your borrowing goals with flexible loan amounts and tenures. "
                f"Estimated monthly repayment spans ₹{emi_min:,.0f} to ₹{emi_max:,.0f} depending on lender credit evaluation."
            )
            fin_impact = (
                f"For ₹{fin_calc.get('requested_amount', 0.0):,.0f} over {fin_calc.get('requested_tenure_months', 0)} months, "
                f"total interest cost is estimated between ₹{fin_calc.get('total_interest_min', 0.0):,.0f} and ₹{fin_calc.get('total_interest_max', 0.0):,.0f}."
            )

        priority_fit = " ".join(matched) if matched else "General match against your financial criteria."
        drawbacks = mismatches if mismatches else [
            "Interest charges apply if balances are not cleared by the due date.",
            "Eligibility criteria published are subject to internal bank credit verification."
        ]

        elig_desc = {
            "meets_published_criteria": "You meet all verified published eligibility requirements for this product.",
            "may_meet_criteria": "You appear compatible, but final approval depends on internal bank underwriting and score checks.",
            "does_not_meet_published_criteria": "You fall below one or more published minimum criteria for this product."
        }.get(status, "Eligibility requires confirmation with the institution.")

        return ExplanationOut(
            why_it_matches=why_it_matches,
            priority_fit=priority_fit,
            financial_impact=fin_impact,
            rank_reasoning=f"Calculated match score of {scored_data.get('match_score', 0):.1f}/100 based on verified data.",
            drawbacks_and_tradeoffs=drawbacks,
            eligibility_limitations=elig_desc,
            assumptions=assumptions,
            what_to_verify_before_applying=[
                "Confirm the latest fee schedule and interest rates on the official bank application portal.",
                "Verify required KYC and income documentation (e.g., 3 months salary slips, Form 16)."
            ],
            official_sources=[{"title": f"Official {issuer} Portal", "url": canonical_url}]
        )
