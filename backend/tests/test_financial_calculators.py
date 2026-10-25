"""
Unit tests for deterministic financial calculators:
- Loan EMI, amortisation schedule, zero interest, and rate ranges.
- Credit card reward calculation, spending caps, fee waivers, and net benefit.
"""
import pytest
from backend.app.schemas.product import CreditCardTerms
from backend.app.schemas.profile import SpendingDistribution
from backend.app.services.loan_calculator import (
    calculate_monthly_emi,
    calculate_loan_schedule,
    calculate_loan_range_metrics,
)
from backend.app.services.card_value_calculator import calculate_credit_card_annual_value


def test_calculate_monthly_emi_standard():
    # Example: 10 Lakh (1,000,000) at 12% pa for 24 months (2 years)
    # Monthly rate = 0.01
    # EMI = 1,000,000 * 0.01 * (1.01)^24 / ((1.01)^24 - 1)
    # = 47,073.47
    emi = calculate_monthly_emi(1000000.0, 12.0, 24)
    assert emi == pytest.approx(47073.47, abs=1.0)


def test_calculate_monthly_emi_zero_interest():
    # 0% interest loan (e.g. no-cost EMI): ₹1,20,000 for 12 months = ₹10,000/mo
    emi = calculate_monthly_emi(120000.0, 0.0, 12)
    assert emi == 10000.0


def test_calculate_monthly_emi_invalid():
    with pytest.raises(ValueError):
        calculate_monthly_emi(-10000, 10.0, 12)
    with pytest.raises(ValueError):
        calculate_monthly_emi(10000, -5.0, 12)
    with pytest.raises(ValueError):
        calculate_monthly_emi(10000, 10.0, 0)


def test_calculate_loan_schedule_with_processing_fee():
    # 3 Lakh (300,000) at 10.5% for 36 months, 1.5% fee + 18% GST
    schedule = calculate_loan_schedule(
        principal=300000.0,
        annual_interest_rate_pct=10.5,
        tenure_months=36,
        processing_fee_pct=1.5,
        min_processing_fee=1000.0,
        max_processing_fee=10000.0
    )
    assert schedule["monthly_emi"] > 0
    assert schedule["total_repayment"] > 300000.0
    assert schedule["total_interest"] == round(schedule["total_repayment"] - 300000.0, 2)
    # Base fee = 1.5% of 300,000 = 4,500
    assert schedule["processing_fee_base"] == 4500.0
    # GST = 18% of 4500 = 810
    assert schedule["processing_fee_gst"] == 810.0
    assert schedule["total_processing_fee"] == 5310.0


def test_calculate_loan_range_metrics():
    metrics = calculate_loan_range_metrics(
        principal=500000.0,
        interest_rate_min=10.5,
        interest_rate_max=16.0,
        tenure_months=24,
        monthly_income=75000.0,
        existing_emi=5000.0
    )
    assert metrics["estimated_emi_min"] < metrics["estimated_emi_max"]
    assert metrics["total_interest_min"] < metrics["total_interest_max"]
    assert metrics["foir_min_pct"] is not None
    assert metrics["foir_max_pct"] is not None
    assert metrics["foir_max_pct"] > metrics["foir_min_pct"]
    assert len(metrics["assumptions"]) >= 3


def test_credit_card_annual_value_basic():
    terms = CreditCardTerms(
        joining_fee=500.0,
        annual_fee=500.0,
        fee_waiver_spend_threshold=100000.0,
        base_cashback_pct=1.0,
        grocery_cashback_pct=5.0,
        online_shopping_cashback_pct=5.0,
        travel_cashback_pct=2.0,
        dining_cashback_pct=3.0,
        fuel_surcharge_waiver_pct=1.0,
        monthly_reward_cap=2000.0,
        welcome_bonus_value=500.0
    )
    spending = SpendingDistribution(
        food_groceries=10000.0,  # 5% = 500
        online_shopping=8000.0,  # 5% = 400
        travel=2000.0,           # 2% = 40
        dining_entertainment=3000.0, # 3% = 90
        fuel=2000.0,             # 1% = 20
        utility_bills=2000.0,    # 1% = 20
        other=1000.0             # 1% = 10
        # Total monthly = 28,000 -> monthly reward = 1080 (below 2000 cap)
        # Annual spend = 28,000 * 12 = 336,000 (exceeds 100,000 waiver threshold!)
    )
    result = calculate_credit_card_annual_value(terms, spending)
    
    assert result["total_monthly_spend"] == 28000.0
    assert result["estimated_annual_spend"] == 336000.0
    assert result["monthly_rewards"] == 1080.0
    assert result["estimated_annual_rewards"] == 12960.0
    assert result["fee_waived"] is True
    assert result["annual_fee_effective"] == 0.0
    assert result["net_annual_benefit"] == 12960.0
    # First year net benefit = 12960 + 500 (welcome) - 500 (joining fee) = 12960
    assert result["first_year_net_benefit"] == 12960.0


def test_credit_card_annual_value_fee_not_waived_and_cap():
    terms = CreditCardTerms(
        joining_fee=1000.0,
        annual_fee=1000.0,
        fee_waiver_spend_threshold=300000.0,
        base_cashback_pct=1.0,
        grocery_cashback_pct=10.0,
        monthly_reward_cap=500.0  # Tight cap
    )
    spending = SpendingDistribution(
        food_groceries=15000.0,  # 10% = 1500, but cap is 500
        online_shopping=0.0
    )
    result = calculate_credit_card_annual_value(terms, spending)
    # Total annual spend = 15,000 * 12 = 180,000 < 300,000 threshold -> fee not waived
    assert result["fee_waived"] is False
    assert result["annual_fee_effective"] == 1000.0
    # Monthly reward capped at 500 -> annual rewards = 6000
    assert result["monthly_rewards"] == 500.0
    assert result["estimated_annual_rewards"] == 6000.0
    assert result["net_annual_benefit"] == 5000.0  # 6000 - 1000
    assert result["reward_cap_applied"] is True
