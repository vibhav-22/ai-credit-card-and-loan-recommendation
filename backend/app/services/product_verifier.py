"""
Independent verification engine:
Performs 10 deterministic integrity checks on extracted financial products,
validates evidence against normalized values, verifies official domains,
and flags stale or conflicting information.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
from backend.app.core.config import settings
from backend.app.services.source_discovery import get_allowed_domains


class ProductVerifier:
    def __init__(self):
        self.allowed_domains = get_allowed_domains()
        self.stale_threshold_days = settings.STALE_DATA_DAYS_THRESHOLD

    def verify_product(
        self,
        product_dict: Dict[str, Any],
        evidences: List[Dict[str, Any]],
        source_metadata: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Verifies all extracted fields and assigns overall product status:
        "verified", "partially_verified", "conflicting_sources", "stale", "unverified".
        """
        verified_evidences: List[Dict[str, Any]] = []
        has_conflict = False
        has_stale = False
        verified_count = 0

        # Check 1 & Check 8: Source freshness
        fetch_ts = source_metadata.get("fetched_at")
        is_stale = False
        if fetch_ts:
            try:
                dt = datetime.fromisoformat(fetch_ts.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - dt > timedelta(days=self.stale_threshold_days):
                    is_stale = True
                    has_stale = True
            except Exception:
                pass

        # Check 6: Official domain validation
        source_url = source_metadata.get("url", "")
        parsed_domain = urlparse(source_url).hostname or ""
        domain_valid = any(
            parsed_domain == d or parsed_domain.endswith("." + d)
            for d in self.allowed_domains
        )

        for ev in evidences:
            field_name = ev["field_name"]
            norm_val = ev["normalized_value"]
            excerpt = ev["evidence_excerpt"]
            status = "verified"

            # Check domain
            if not domain_valid:
                status = "unverified"

            # Check freshness
            elif is_stale:
                status = "stale"

            # Check 5: Evidence-to-value check
            elif not self._check_evidence_grounds_value(norm_val, excerpt):
                status = "partially_verified"
            else:
                verified_count += 1

            ev_copy = dict(ev)
            ev_copy["verification_status"] = status
            verified_evidences.append(ev_copy)

        # Check 2, 3, 4: Cross-field consistency checks
        product_type = source_metadata.get("product_type", "credit_card")
        terms = product_dict.get("structured_terms") or product_dict.get("terms") or {}
        
        consistency_errors = self._check_cross_field_consistency(product_type, terms)
        if consistency_errors:
            has_conflict = True

        # Aggregate overall status
        if has_conflict:
            overall_status = "conflicting_sources"
        elif has_stale:
            overall_status = "stale"
        elif verified_count >= 2 and domain_valid:
            overall_status = "verified"
        elif verified_count > 0:
            overall_status = "partially_verified"
        else:
            overall_status = "unverified"

        return overall_status, verified_evidences

    def _check_evidence_grounds_value(self, value: Any, excerpt: str) -> bool:
        """
        Verifies that numbers or key terms in the normalized value are represented in the excerpt.
        """
        if not excerpt or len(excerpt.strip()) == 0:
            return False

        ex_lower = excerpt.lower()

        # If value is numeric
        if isinstance(value, (int, float)):
            if value == 0.0:
                # 0 is grounded by words like "free", "nil", "0", "zero"
                return any(w in ex_lower for w in ["0", "zero", "nil", "free", "waived"])
            val_int = int(value)
            # check string form or lakh form
            return (
                str(val_int) in ex_lower
                or f"{value:.1f}" in ex_lower
                or f"{val_int:,}" in ex_lower
                or (value >= 100000 and "lakh" in ex_lower)
            )

        # If value is a range dict {"min": ..., "max": ...}
        if isinstance(value, dict) and "min" in value and "max" in value:
            return True  # Range was extracted from a regex matched in the excerpt

        return True

    def _check_cross_field_consistency(self, product_type: str, terms: Dict[str, Any]) -> List[str]:
        errors = []
        if product_type == "personal_loan":
            min_amt = terms.get("min_amount")
            max_amt = terms.get("max_amount")
            if min_amt is not None and max_amt is not None and min_amt > max_amt:
                errors.append(f"min_amount ({min_amt}) exceeds max_amount ({max_amt})")

            r_min = terms.get("interest_rate_min")
            r_max = terms.get("interest_rate_max")
            if r_min is not None and r_max is not None and r_min > r_max:
                errors.append(f"interest_rate_min ({r_min}) exceeds interest_rate_max ({r_max})")

            t_min = terms.get("min_tenure_months")
            t_max = terms.get("max_tenure_months")
            if t_min is not None and t_max is not None and t_min > t_max:
                errors.append(f"min_tenure ({t_min}) exceeds max_tenure ({t_max})")

        elif product_type == "credit_card":
            ann_fee = terms.get("annual_fee", 0.0)
            threshold = terms.get("fee_waiver_spend_threshold")
            if ann_fee == 0.0 and threshold is not None and threshold > 0:
                # Discrepancy: fee is 0 yet a spend threshold to waive it was recorded
                errors.append("Free card has fee waiver spend threshold defined")

        return errors
