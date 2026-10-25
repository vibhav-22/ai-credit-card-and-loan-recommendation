"""
Unit tests for Profile Parser and Adaptive Clarification Engine.
"""
import pytest
from backend.app.services.profile_parser import ProfileParser
from backend.app.services.profile_clarifier import ProfileClarifier


@pytest.mark.asyncio
async def test_parse_profile_credit_card_user():
    parser = ProfileParser()
    message = (
        "I'm 24, working in Bengaluru and earning around ₹65,000 per month. "
        "My salary comes into an HDFC account. I spend about ₹8,000 on food and groceries, "
        "₹5,000 on online shopping, and ₹4,000 on travel every month. "
        "I want a credit card with good cashback, no joining fee if possible, and preferably a low annual fee. "
        "My credit score is approximately 760. I don't want to pay interest or carry a balance."
    )
    profile = await parser.parse_profile(message)
    
    assert profile.monthly_income is not None
    assert profile.monthly_income.value == 65000.0
    assert profile.monthly_income.source == "user_provided"
    assert profile.credit_score is not None
    assert profile.credit_score.value == 760
    assert profile.employment_type.value == "salaried"
    assert profile.spending.food_groceries == 8000.0
    assert profile.spending.online_shopping == 5000.0
    assert profile.card_preferences.low_annual_fee is True
    assert profile.card_preferences.avoid_interest is True


@pytest.mark.asyncio
async def test_parse_profile_loan_user():
    parser = ProfileParser()
    message = (
        "I need a personal loan of ₹3 lakh for 24 months. I earn ₹55,000 monthly, "
        "work at a private company, have an existing EMI of ₹7,000, and want to minimize the total interest paid. "
        "I prefer lenders with transparent charges and no hidden fees."
    )
    profile = await parser.parse_profile(message)

    assert profile.preferred_product in ("personal_loan", "both")
    assert profile.loan_preferences.requested_amount == 300000.0
    assert profile.loan_preferences.requested_tenure_months == 24
    assert profile.monthly_income.value == 55000.0
    assert profile.existing_monthly_emi.value == 7000.0


@pytest.mark.asyncio
async def test_profile_parser_correction_merge():
    parser = ProfileParser()
    first_message = "I make 50k per month and want a credit card with low fees."
    profile = await parser.parse_profile(first_message)
    assert profile.monthly_income.value == 50000.0

    # User corrects income to 70k
    followup_message = "Actually, my monthly salary just increased to ₹70,000."
    updated_profile = await parser.parse_profile(followup_message, current_profile=profile)
    assert updated_profile.monthly_income.value == 70000.0
    # Prior card preferences are preserved
    assert updated_profile.card_preferences.low_annual_fee is True


def test_clarifier_complete_profile():
    clarifier = ProfileClarifier()
    parser = ProfileParser()
    
    # Fully specified card profile
    from backend.app.schemas.profile import FinancialProfile, ProvenanceValue, SpendingDistribution
    profile = FinancialProfile(
        monthly_income=ProvenanceValue(value=65000.0, source="user_provided"),
        credit_score=ProvenanceValue(value=760, source="user_provided"),
        employment_type=ProvenanceValue(value="salaried", source="user_provided"),
        preferred_product="credit_card",
        spending=SpendingDistribution(food_groceries=5000.0, online_shopping=3000.0)
    )
    
    resp = clarifier.evaluate(profile)
    assert resp.profile_complete is True
    assert len(resp.questions) == 0


def test_clarifier_missing_loan_details():
    clarifier = ProfileClarifier()
    from backend.app.schemas.profile import FinancialProfile, ProvenanceValue
    profile = FinancialProfile(
        monthly_income=ProvenanceValue(value=65000.0, source="user_provided"),
        preferred_product="personal_loan"
    )
    resp = clarifier.evaluate(profile)
    assert resp.profile_complete is False
    # Should ask for loan amount and tenure, at most 3 questions
    assert 1 <= len(resp.questions) <= 3
    fields = [q.field for q in resp.questions]
    assert "requested_amount" in fields or "requested_tenure_months" in fields


@pytest.mark.asyncio
async def test_student_credit_score_does_not_ask_loan():
    parser = ProfileParser()
    clarifier = ProfileClarifier()
    profile = await parser.parse_profile("credit score for a 20 y/o student")
    assert profile.preferred_product == "credit_card"
    assert profile.age is not None and profile.age.value == 20
    assert profile.employment_type is not None and profile.employment_type.value == "student"

    resp = clarifier.evaluate(profile)
    fields = [q.field for q in resp.questions]
    # Loan fields must NOT be asked
    assert "requested_amount" not in fields
    assert "requested_tenure_months" not in fields
