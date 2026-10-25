"""
Deterministic loan calculation utilities:
- Amortizing EMI formula with zero-interest handling
- Total scheduled interest and repayments
- Processing fees with GST and caps
- Illustrative rate range calculations
- Debt-to-income (FOIR) ratios
"""
from typing import Dict, Any, Optional, Tuple


def calculate_monthly_emi(principal: float, annual_interest_rate_pct: float, tenure_months: int) -> float:
    """
    Calculates monthly EMI using standard amortizing loan formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    
    If annual_interest_rate_pct is 0, EMI = P / n
    """
    if principal <= 0 or tenure_months <= 0:
        raise ValueError("Principal and tenure_months must be greater than zero.")
    
    if annual_interest_rate_pct < 0:
        raise ValueError("Interest rate cannot be negative.")
        
    if annual_interest_rate_pct == 0.0:
        return round(principal / tenure_months, 2)

    # Monthly interest rate as a fraction
    monthly_rate = (annual_interest_rate_pct / 100.0) / 12.0
    
    compound_factor = (1.0 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * compound_factor / (compound_factor - 1.0)
    return round(emi, 2)


def calculate_loan_schedule(
    principal: float,
    annual_interest_rate_pct: float,
    tenure_months: int,
    processing_fee_pct: float = 0.0,
    min_processing_fee: Optional[float] = None,
    max_processing_fee: Optional[float] = None,
    apply_gst_on_fee: bool = True
) -> Dict[str, Any]:
    """
    Calculates complete loan repayment breakdown for a specific annual interest rate.
    """
    emi = calculate_monthly_emi(principal, annual_interest_rate_pct, tenure_months)
    total_repayment = round(emi * tenure_months, 2)
    total_interest = round(total_repayment - principal, 2)
    
    # Calculate processing fee
    fee = principal * (processing_fee_pct / 100.0)
    if min_processing_fee is not None and fee < min_processing_fee:
        fee = min_processing_fee
    if max_processing_fee is not None and fee > max_processing_fee:
        fee = max_processing_fee
        
    gst_fee = round(fee * 0.18, 2) if apply_gst_on_fee else 0.0
    total_processing_fee = round(fee + gst_fee, 2)
    
    total_borrowing_cost = round(total_interest + total_processing_fee, 2)
    
    return {
        "principal": principal,
        "annual_interest_rate_pct": annual_interest_rate_pct,
        "tenure_months": tenure_months,
        "monthly_emi": emi,
        "total_repayment": total_repayment,
        "total_interest": total_interest,
        "processing_fee_base": round(fee, 2),
        "processing_fee_gst": gst_fee,
        "total_processing_fee": total_processing_fee,
        "total_borrowing_cost": total_borrowing_cost,
    }


def calculate_loan_range_metrics(
    principal: float,
    interest_rate_min: float,
    interest_rate_max: float,
    tenure_months: int,
    processing_fee_pct: float = 1.5,
    min_processing_fee: Optional[float] = 1000.0,
    max_processing_fee: Optional[float] = 15000.0,
    monthly_income: Optional[float] = None,
    existing_emi: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Produces full illustrative metric range for loan recommendations,
    accounting for minimum and maximum advertised rates.
    """
    min_schedule = calculate_loan_schedule(
        principal=principal,
        annual_interest_rate_pct=interest_rate_min,
        tenure_months=tenure_months,
        processing_fee_pct=processing_fee_pct,
        min_processing_fee=min_processing_fee,
        max_processing_fee=max_processing_fee
    )
    
    max_schedule = calculate_loan_schedule(
        principal=principal,
        annual_interest_rate_pct=interest_rate_max,
        tenure_months=tenure_months,
        processing_fee_pct=processing_fee_pct,
        min_processing_fee=min_processing_fee,
        max_processing_fee=max_processing_fee
    )

    # Debt-to-income (FOIR) calculations if monthly income is provided
    foir_min = None
    foir_max = None
    if monthly_income and monthly_income > 0:
        curr_emi = existing_emi or 0.0
        foir_min = round(((curr_emi + min_schedule["monthly_emi"]) / monthly_income) * 100.0, 1)
        foir_max = round(((curr_emi + max_schedule["monthly_emi"]) / monthly_income) * 100.0, 1)

    return {
        "requested_amount": principal,
        "requested_tenure_months": tenure_months,
        "estimated_emi_min": min_schedule["monthly_emi"],
        "estimated_emi_max": max_schedule["monthly_emi"],
        "total_repayment_min": min_schedule["total_repayment"],
        "total_repayment_max": max_schedule["total_repayment"],
        "total_interest_min": min_schedule["total_interest"],
        "total_interest_max": max_schedule["total_interest"],
        "estimated_processing_fee": min_schedule["total_processing_fee"],
        "is_zero_interest": (interest_rate_min == 0.0 and interest_rate_max == 0.0),
        "foir_min_pct": foir_min,
        "foir_max_pct": foir_max,
        "assumptions": [
            f"Amortizing loan calculation for ₹{principal:,.0f} over {tenure_months} months.",
            f"Advertised nominal interest rate range is {interest_rate_min:.2f}% to {interest_rate_max:.2f}% p.a.",
            "Actual rate offered is subject to lender credit appraisal, employer category, and CIBIL score.",
            "Processing fee includes 18% standard GST.",
        ]
    }
