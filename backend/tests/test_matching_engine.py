"""
Unit tests for Eligibility Engine and Deterministic Matching & Ranking Engine.
"""
from backend.app.schemas.profile import (
    FinancialProfile,
    ProvenanceValue,
    SpendingDistribution,
    CardPreferences,
    LoanPreferences,
)
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.eligibility_engine import EligibilityEngine


def test_eligibility_engine_income_and_age():
    engine = EligibilityEngine()
    profile = FinancialProfile(
        monthly_income=ProvenanceValue(value=25000.0, source="user_provided"),
        age=ProvenanceValue(value=26, source="user_provided")
    )
    terms_pass = {"min_monthly_income": 20000.0, "min_age": 21, "max_age": 60}
    res_pass = engine.evaluate(profile, terms_pass)
    assert res_pass.status == "meets_published_criteria"
    assert res_pass.score == 100.0

    terms_fail = {"min_monthly_income": 35000.0}
    res_fail = engine.evaluate(profile, terms_fail)
    assert res_fail.status == "does_not_meet_published_criteria"
    assert res_fail.score == 0.0


def test_matching_engine_cashback_preference():
    engine = MatchingEngine()
    # User spends 20k/mo on online shopping & groceries, wants cashback & low fee
    profile = FinancialProfile(
        monthly_income=ProvenanceValue(value=75000.0, source="user_provided"),
        preferred_product="credit_card",
        spending=SpendingDistribution(food_groceries=10000.0, online_shopping=10000.0),
        card_preferences=CardPreferences(cashback_priority=True, low_annual_fee=True)
    )

    card_a = {
        "id": "card_a",
        "product_name": "Premium High Fee Travel Card",
        "product_type": "credit_card",
        "issuer": "Bank A",
        "structured_terms": {
            "joining_fee": 5000.0,
            "annual_fee": 5000.0,
            "base_cashback_pct": 1.0,
            "online_shopping_cashback_pct": 1.0,
            "min_monthly_income": 50000.0
        },
        "data_quality_status": "verified"
    }

    card_b = {
        "id": "card_b",
        "product_name": "Online Cashback Champion",
        "product_type": "credit_card",
        "issuer": "Bank B",
        "structured_terms": {
            "joining_fee": 500.0,
            "annual_fee": 500.0,
            "fee_waiver_spend_threshold": 100000.0,
            "base_cashback_pct": 1.0,
            "grocery_cashback_pct": 5.0,
            "online_shopping_cashback_pct": 5.0,
            "min_monthly_income": 30000.0
        },
        "data_quality_status": "verified"
    }

    ranked = engine.evaluate_and_rank_products(profile, [card_a, card_b])
    assert len(ranked) == 2
    # Card B should rank #1 because it has 5% cashback, fee waiver, and lower fee
    assert ranked[0]["product_id"] == "card_b"
    assert ranked[0]["match_score"] > ranked[1]["match_score"]


def test_matching_engine_deterministic_reproducibility():
    engine = MatchingEngine()
    profile = FinancialProfile(
        monthly_income=ProvenanceValue(value=60000.0, source="user_provided"),
        preferred_product="personal_loan",
        loan_preferences=LoanPreferences(requested_amount=300000.0, requested_tenure_months=24)
    )

    loan_1 = {
        "id": "l1",
        "product_name": "Loan Option Alpha",
        "product_type": "personal_loan",
        "issuer": "Bank Alpha",
        "structured_terms": {
            "min_amount": 50000.0,
            "max_amount": 2000000.0,
            "interest_rate_min": 10.5,
            "interest_rate_max": 14.0,
            "min_tenure_months": 12,
            "max_tenure_months": 60,
            "processing_fee_pct": 1.5,
            "min_monthly_income": 25000.0
        },
        "data_quality_status": "verified"
    }

    loan_2 = {
        "id": "l2",
        "product_name": "Loan Option Beta",
        "product_type": "personal_loan",
        "issuer": "Bank Beta",
        "structured_terms": {
            "min_amount": 50000.0,
            "max_amount": 1000000.0,
            "interest_rate_min": 15.0,
            "interest_rate_max": 20.0,
            "min_tenure_months": 12,
            "max_tenure_months": 48,
            "processing_fee_pct": 2.5,
            "min_monthly_income": 25000.0
        },
        "data_quality_status": "verified"
    }

    run1 = engine.evaluate_and_rank_products(profile, [loan_1, loan_2])
    run2 = engine.evaluate_and_rank_products(profile, [loan_2, loan_1])  # inverted input order

    # Both runs should yield identical top product and scores
    assert run1[0]["product_id"] == run2[0]["product_id"]
    assert run1[0]["match_score"] == run2[0]["match_score"]
    assert run1[1]["match_score"] == run2[1]["match_score"]
    assert run1[0]["product_id"] == "l1"  # lower rate loan wins
