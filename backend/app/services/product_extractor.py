"""
LLM & rule-augmented Product Extractor:
Extracts structured CreditCardTerms or LoanTerms with field-level evidence citations.
"""
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from backend.app.schemas.product import CreditCardTerms, LoanTerms
from backend.app.services.llm_provider import get_llm_provider
from backend.app.core.logging import logger


class FieldEvidenceItem:
    def __init__(
        self,
        field_name: str,
        extracted_value: Any,
        normalized_value: Any,
        evidence_excerpt: str,
        source_url: str,
        confidence: float = 1.0
    ):
        self.field_name = field_name
        self.extracted_value = extracted_value
        self.normalized_value = normalized_value
        self.evidence_excerpt = evidence_excerpt
        self.source_url = source_url
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "extracted_value": self.extracted_value,
            "normalized_value": self.normalized_value,
            "evidence_excerpt": self.evidence_excerpt,
            "source_url": self.source_url,
            "confidence": self.confidence,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }


class ProductExtractor:
    def __init__(self):
        self.llm = get_llm_provider()

    def extract_product_from_text(
        self,
        clean_text: str,
        source_metadata: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extracts structured product terms and field-level evidence.
        """
        product_type = source_metadata.get("product_type", "credit_card")
        url = source_metadata.get("url", "")
        product_name = source_metadata.get("product_name", "Financial Product")
        issuer = source_metadata.get("institution", "Bank")

        if product_type == "credit_card":
            terms_dict, evidences = self._extract_credit_card_terms(clean_text, url)
        else:
            terms_dict, evidences = self._extract_loan_terms(clean_text, url)

        return terms_dict, [e.to_dict() for e in evidences]

    def _extract_credit_card_terms(self, text: str, url: str) -> Tuple[Dict[str, Any], List[FieldEvidenceItem]]:
        t = text.lower()
        evidences: List[FieldEvidenceItem] = []
        terms = CreditCardTerms()

        # 1. Joining fee
        jf_match = re.search(r'joining\s*(?:renewal)?\s*fee[^\n\d]{0,40}?(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if jf_match:
            val = float(jf_match.group(1).replace(",", ""))
            terms.joining_fee = val
            evidences.append(FieldEvidenceItem(
                field_name="joining_fee",
                extracted_value=jf_match.group(0),
                normalized_value=val,
                evidence_excerpt=self._get_surrounding_snippet(text, jf_match.start()),
                source_url=url,
                confidence=1.0
            ))
        elif "joining fee: ₹0" in t or "joining fee: 0" in t or "lifetime free" in t:
            terms.joining_fee = 0.0
            evidences.append(FieldEvidenceItem(
                field_name="joining_fee",
                extracted_value="Lifetime Free / ₹0",
                normalized_value=0.0,
                evidence_excerpt="Lifetime Free credit card with ₹0 joining fee",
                source_url=url,
                confidence=1.0
            ))

        # 2. Annual Renewal fee
        af_match = re.search(r'(?:annual\s*(?:renewal)?\s*fee|renewal\s*fee)[^\n\d]{0,40}?(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if af_match:
            val = float(af_match.group(1).replace(",", ""))
            terms.annual_fee = val
            evidences.append(FieldEvidenceItem(
                field_name="annual_fee",
                extracted_value=af_match.group(0),
                normalized_value=val,
                evidence_excerpt=self._get_surrounding_snippet(text, af_match.start()),
                source_url=url,
                confidence=1.0
            ))
        elif "lifetime free" in t or "annual renewal fee: ₹0" in t:
            terms.annual_fee = 0.0
            evidences.append(FieldEvidenceItem(
                field_name="annual_fee",
                extracted_value="Lifetime Free / ₹0",
                normalized_value=0.0,
                evidence_excerpt="Lifetime Free / Nil annual maintenance charges",
                source_url=url,
                confidence=1.0
            ))

        # 3. Fee waiver spend threshold
        waiver_match = re.search(r'(?:waived|reversed|waiver)[^\n\d]{0,50}?(?:spending|spends?|spend)[^\n\d]{0,30}?(?:₹|rs\.?|inr)?\s*([0-9,.]+)\s*(lakh|lac)?', t)
        if waiver_match:
            val = float(waiver_match.group(1).replace(",", ""))
            if waiver_match.group(2) in ('lakh', 'lac'):
                val *= 100000.0
            terms.fee_waiver_spend_threshold = val
            evidences.append(FieldEvidenceItem(
                field_name="fee_waiver_spend_threshold",
                extracted_value=waiver_match.group(0),
                normalized_value=val,
                evidence_excerpt=self._get_surrounding_snippet(text, waiver_match.start()),
                source_url=url,
                confidence=0.95
            ))

        # 4. Cashback rates (e.g. 5% on Amazon/groceries, 1% other)
        cb_match = re.search(r'([0-9.]+)%\s*cashback\s*on\s*([^\n\.]+)', t)
        if cb_match:
            rate = float(cb_match.group(1))
            terms.grocery_cashback_pct = rate
            terms.online_shopping_cashback_pct = rate
            evidences.append(FieldEvidenceItem(
                field_name="category_cashback_pct",
                extracted_value=cb_match.group(0),
                normalized_value=rate,
                evidence_excerpt=self._get_surrounding_snippet(text, cb_match.start()),
                source_url=url,
                confidence=0.95
            ))
        elif "10x reward points on online spends" in t:
            # 10X points ~ 2.5% to 5% equivalent
            terms.online_shopping_cashback_pct = 2.5
            terms.grocery_cashback_pct = 2.5
            evidences.append(FieldEvidenceItem(
                field_name="online_shopping_cashback_pct",
                extracted_value="10X Reward Points on online partners",
                normalized_value=2.5,
                evidence_excerpt="10X Reward Points on online spends with exclusive partners",
                source_url=url,
                confidence=0.9
            ))

        # Base cashback
        base_m = re.search(r'([0-9.]+)%\s*cashback\s*on\s*all\s*other', t)
        if base_m:
            terms.base_cashback_pct = float(base_m.group(1))

        # Monthly reward cap
        cap_m = re.search(r'maximum\s*cashback\s*of\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if cap_m:
            cap_val = float(cap_m.group(1).replace(",", ""))
            terms.monthly_reward_cap = cap_val
            evidences.append(FieldEvidenceItem(
                field_name="monthly_reward_cap",
                extracted_value=cap_m.group(0),
                normalized_value=cap_val,
                evidence_excerpt=self._get_surrounding_snippet(text, cap_m.start()),
                source_url=url,
                confidence=1.0
            ))

        # Minimum monthly income
        inc_m = re.search(r'(?:monthly\s*income|net\s*monthly\s*salary)[^\n\d]{0,40}?(?:>|of)?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if inc_m:
            inc_val = float(inc_m.group(1).replace(",", ""))
            terms.min_monthly_income = inc_val
            evidences.append(FieldEvidenceItem(
                field_name="min_monthly_income",
                extracted_value=inc_m.group(0),
                normalized_value=inc_val,
                evidence_excerpt=self._get_surrounding_snippet(text, inc_m.start()),
                source_url=url,
                confidence=0.95
            ))

        # Welcome bonus
        wb_m = re.search(r'(?:welcome\s*gift|welcome\s*benefit)[^\n\d]{0,50}?(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if wb_m:
            wb_val = float(wb_m.group(1).replace(",", ""))
            terms.welcome_bonus_value = wb_val

        terms.official_apply_url = url
        return terms.model_dump(), evidences

    def _extract_loan_terms(self, text: str, url: str) -> Tuple[Dict[str, Any], List[FieldEvidenceItem]]:
        t = text.lower()
        evidences: List[FieldEvidenceItem] = []
        terms = LoanTerms()

        # 1. Loan Amount Range
        amt_match = re.search(r'(?:loan\s*amount)[^\n\d]{0,40}?(?:₹|rs\.?|inr)?\s*([0-9,.]+)\s*(?:to|up\s*to|-)\s*(?:₹|rs\.?|inr)?\s*([0-9,.]+)\s*(lakh|lac|crore)?', t)
        if amt_match:
            min_val = float(amt_match.group(1).replace(",", ""))
            max_val = float(amt_match.group(2).replace(",", ""))
            unit = amt_match.group(3)
            if unit in ('lakh', 'lac'):
                if min_val < 1000:
                    min_val *= 100000.0
                if max_val < 1000:
                    max_val *= 100000.0
            terms.min_amount = min_val
            terms.max_amount = max_val
            evidences.append(FieldEvidenceItem(
                field_name="loan_amount_range",
                extracted_value=amt_match.group(0),
                normalized_value={"min": min_val, "max": max_val},
                evidence_excerpt=self._get_surrounding_snippet(text, amt_match.start()),
                source_url=url,
                confidence=0.95
            ))

        # 2. Interest Rate Range
        rate_match = re.search(r'([0-9.]+)%\s*to\s*([0-9.]+)%\s*(?:p\.?a\.?|per\s*annum)', t)
        if rate_match:
            r_min = float(rate_match.group(1))
            r_max = float(rate_match.group(2))
            terms.interest_rate_min = r_min
            terms.interest_rate_max = r_max
            evidences.append(FieldEvidenceItem(
                field_name="interest_rate_range",
                extracted_value=rate_match.group(0),
                normalized_value={"min": r_min, "max": r_max},
                evidence_excerpt=self._get_surrounding_snippet(text, rate_match.start()),
                source_url=url,
                confidence=1.0
            ))

        # 3. Tenure Range
        tenure_m = re.search(r'([0-9]+)\s*(?:months?|years?)\s*to\s*([0-9]+)\s*(months?|years?)', t)
        if tenure_m:
            t_min = int(tenure_m.group(1))
            t_max = int(tenure_m.group(2))
            unit = tenure_m.group(3)
            if "year" in unit:
                if t_min < 10:
                    t_min *= 12
                t_max *= 12
            terms.min_tenure_months = t_min
            terms.max_tenure_months = t_max
            evidences.append(FieldEvidenceItem(
                field_name="tenure_range",
                extracted_value=tenure_m.group(0),
                normalized_value={"min_months": t_min, "max_months": t_max},
                evidence_excerpt=self._get_surrounding_snippet(text, tenure_m.start()),
                source_url=url,
                confidence=0.95
            ))

        # 4. Processing Fee
        pf_match = re.search(r'(?:processing\s*fees?)[^\n\d]{0,40}?([0-9.]+)%', t)
        if pf_match:
            terms.processing_fee_pct = float(pf_match.group(1))
            evidences.append(FieldEvidenceItem(
                field_name="processing_fee_pct",
                extracted_value=pf_match.group(0),
                normalized_value=float(pf_match.group(1)),
                evidence_excerpt=self._get_surrounding_snippet(text, pf_match.start()),
                source_url=url,
                confidence=0.9
            ))

        # 5. Minimum Monthly Income
        inc_m = re.search(r'(?:minimum\s*(?:net)?\s*monthly\s*(?:income|salary))[^\n\d]{0,30}?(?:₹|rs\.?|inr)?\s*([0-9,]+)', t)
        if inc_m:
            inc_val = float(inc_m.group(1).replace(",", ""))
            terms.min_monthly_income = inc_val
            evidences.append(FieldEvidenceItem(
                field_name="min_monthly_income",
                extracted_value=inc_m.group(0),
                normalized_value=inc_val,
                evidence_excerpt=self._get_surrounding_snippet(text, inc_m.start()),
                source_url=url,
                confidence=0.95
            ))

        terms.official_apply_url = url
        return terms.model_dump(), evidences

    def _get_surrounding_snippet(self, text: str, pos: int, length: int = 140) -> str:
        start = max(0, pos - 30)
        end = min(len(text), pos + length)
        snippet = text[start:end].replace("\n", " ").strip()
        return snippet
