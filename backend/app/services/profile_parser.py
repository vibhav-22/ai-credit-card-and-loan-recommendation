"""
Natural language financial profile parser:
Transforms free-form conversational inputs into validated FinancialProfile objects
with strict provenance, Indian currency/unit normalization, and safe update merging.
"""
import re
from typing import Optional, Dict, Any
from backend.app.schemas.profile import (
    FinancialProfile,
    ProvenanceValue,
    SpendingDistribution,
    CardPreferences,
    LoanPreferences,
)
from backend.app.services.llm_provider import get_llm_provider
from backend.app.core.logging import logger


class ProfileParser:
    def __init__(self):
        self.llm = get_llm_provider()

    async def parse_profile(
        self,
        message: str,
        current_profile: Optional[FinancialProfile] = None,
        category: Optional[str] = None
    ) -> FinancialProfile:
        """
        Parses a conversational user message, updating or creating the financial profile.
        """
        prompt = (
            f"Extract user financial profile from the following user description:\n"
            f"User message: {message}\n"
            f"Requested category: {category or 'unspecified'}\n"
        )
        system_prompt = (
            "You are an expert Indian fintech financial profiler. "
            "Extract monthly income, credit score, employment type, spending distribution, "
            "loan requirements, and financial preferences. Return strictly valid JSON."
        )

        try:
            extracted = await self.llm.generate_json(prompt=prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.warning(f"LLM JSON generation failed, falling back to rule-based parser: {e}")
            from backend.app.services.llm_provider import MockLLMProvider
            extracted = MockLLMProvider()._mock_profile_extraction(message)

        # Merge extracted fields with current_profile if present
        return self._build_and_merge_profile(extracted, current_profile, message, category)

    def _build_and_merge_profile(
        self,
        extracted: Dict[str, Any],
        current: Optional[FinancialProfile],
        raw_message: str,
        requested_category: Optional[str] = None
    ) -> FinancialProfile:
        profile = current.model_copy(deep=True) if current else FinancialProfile()

        # Handle explicit category preference vs natural language intent
        if requested_category and requested_category in ("credit_card", "personal_loan"):
            profile.preferred_product = requested_category
        elif "preferred_product" in extracted and extracted["preferred_product"] in ("credit_card", "personal_loan"):
            profile.preferred_product = extracted["preferred_product"]
        elif requested_category == "both":
            profile.preferred_product = "both"

        # Age
        age_data = extracted.get("age")
        if age_data and isinstance(age_data, dict) and age_data.get("value") is not None:
            profile.age = ProvenanceValue(
                value=int(age_data["value"]),
                source=age_data.get("source", "user_provided"),
                confidence=float(age_data.get("confidence", 1.0))
            )

        # 1. Monthly Income
        inc_data = extracted.get("monthly_income")
        if inc_data and isinstance(inc_data, dict) and inc_data.get("value") is not None:
            profile.monthly_income = ProvenanceValue(
                value=float(inc_data["value"]),
                source=inc_data.get("source", "user_provided"),
                confidence=float(inc_data.get("confidence", 1.0))
            )

        # 2. Employment Type
        emp_data = extracted.get("employment_type")
        if emp_data and isinstance(emp_data, dict) and emp_data.get("value"):
            profile.employment_type = ProvenanceValue(
                value=str(emp_data["value"]),
                source=emp_data.get("source", "user_provided"),
                confidence=float(emp_data.get("confidence", 1.0))
            )

        # 3. Credit Score
        cs_data = extracted.get("credit_score")
        if cs_data and isinstance(cs_data, dict) and cs_data.get("value") is not None:
            profile.credit_score = ProvenanceValue(
                value=int(cs_data["value"]),
                source=cs_data.get("source", "user_provided"),
                confidence=float(cs_data.get("confidence", 1.0))
            )

        # 4. Existing Monthly EMI
        emi_data = extracted.get("existing_monthly_emi")
        if emi_data and isinstance(emi_data, dict) and emi_data.get("value") is not None:
            profile.existing_monthly_emi = ProvenanceValue(
                value=float(emi_data["value"]),
                source=emi_data.get("source", "user_provided"),
                confidence=float(emi_data.get("confidence", 1.0))
            )

        # 5. City
        city_data = extracted.get("city")
        if city_data and isinstance(city_data, dict) and city_data.get("value"):
            profile.city = ProvenanceValue(
                value=str(city_data["value"]),
                source=city_data.get("source", "user_provided"),
                confidence=float(city_data.get("confidence", 0.9))
            )

        # 6. Spending Distribution
        sp = extracted.get("spending", {})
        if sp and isinstance(sp, dict):
            spending_dict = profile.spending.model_dump()
            for k, v in sp.items():
                if k in spending_dict and v is not None and float(v) > 0:
                    spending_dict[k] = float(v)
            profile.spending = SpendingDistribution(**spending_dict)

        # 7. Card Preferences
        cp = extracted.get("card_preferences", {})
        if cp and isinstance(cp, dict):
            card_dict = profile.card_preferences.model_dump()
            for k, v in cp.items():
                if k in card_dict and v is not None:
                    if isinstance(v, bool):
                        if v is True:
                            card_dict[k] = True
                    else:
                        card_dict[k] = v
            profile.card_preferences = CardPreferences(**card_dict)

        # 8. Loan Preferences
        lp = extracted.get("loan_preferences", {})
        if lp and isinstance(lp, dict):
            loan_dict = profile.loan_preferences.model_dump()
            for k, v in lp.items():
                if k in loan_dict and v is not None:
                    if isinstance(v, bool):
                        if v is True:
                            loan_dict[k] = True
                    else:
                        loan_dict[k] = v
            profile.loan_preferences = LoanPreferences(**loan_dict)

        # 9. Perform unit normalization from raw message if user used words like "Lakh" or "k"
        self._refine_with_indian_regex(profile, raw_message)

        return profile

    def _refine_with_indian_regex(self, profile: FinancialProfile, text: str):
        """Supplementary deterministic passes for Indian financial units."""
        t = text.lower()

        # Handle age detection (e.g., '20 y/o', '24 years old', 'age 20')
        if not profile.age or not profile.age.value:
            age_m = re.search(r'(?:\b(?:i am|i\'m|age|aged|am)\s*([0-9]{2})\b|\b([0-9]{2})\s*(?:y/o|yo|yr|yrs|year|years)(?:\s*old)?\b)', t)
            if age_m:
                try:
                    a_val = int(age_m.group(1) or age_m.group(2))
                    if 16 <= a_val <= 99:
                        profile.age = ProvenanceValue(value=a_val, source="user_provided", confidence=1.0)
                except ValueError:
                    pass

        # Handle '15 LPA' or '12 Lakhs annual package'
        lpa_match = re.search(r'([0-9.]+)\s*(?:lpa|lakhs?\s*per\s*annum|lakhs?\s*annual)', t)
        if lpa_match:
            try:
                annual_lakhs = float(lpa_match.group(1))
                monthly_val = round((annual_lakhs * 100000.0) / 12.0, 2)
                profile.monthly_income = ProvenanceValue(
                    value=monthly_val,
                    source="user_provided",
                    confidence=1.0
                )
            except ValueError:
                pass

        # Handle explicit salary updates: "salary increased to ₹70,000" or "earning 70k"
        inc_match = re.search(
            r'(?:salary|income|earning|make|makes|making|take\s*home)(?:\s*(?:is|increased\s*to|became|now|comes\s*to|of|\:))?\s*(?:₹|rs\.?|inr)?\s*([0-9,.]+)\s*(k|lakh|lac)?',
            t
        )
        if inc_match:
            try:
                val = float(inc_match.group(1).replace(",", ""))
                mod = inc_match.group(2)
                if mod == 'k':
                    val *= 1000.0
                elif mod in ('lakh', 'lac'):
                    val *= 100000.0
                profile.monthly_income = ProvenanceValue(
                    value=val,
                    source="user_provided",
                    confidence=1.0
                )
            except ValueError:
                pass

        # Handle direct loan amount only when loan intent exists
        if profile.preferred_product in ("personal_loan", "both") and ("loan" in t or "borrow" in t):
            loan_m = re.search(r'(?:loan\s+(?:of|for)?|borrow|personal\s*loan)\s*(?:₹|rs\.?|inr)?\s*([0-9.]+)\s*(lakh|lac|k)?', t)
            if loan_m:
                try:
                    amt = float(loan_m.group(1))
                    u = loan_m.group(2)
                    if u in ('lakh', 'lac'):
                        amt *= 100000.0
                    elif u == 'k':
                        amt *= 1000.0
                    profile.loan_preferences.requested_amount = amt
                except ValueError:
                    pass
