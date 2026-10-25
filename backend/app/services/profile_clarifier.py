"""
Adaptive clarification engine:
Evaluates a structured FinancialProfile and generates at most 2-3 high-value,
materially relevant clarification questions with quick selectable suggestions.
"""
from typing import List
from backend.app.schemas.profile import (
    FinancialProfile,
    ClarificationQuestion,
    ClarificationResponse,
)


class ProfileClarifier:
    def evaluate(self, profile: FinancialProfile) -> ClarificationResponse:
        questions: List[ClarificationQuestion] = []

        is_student = bool(profile.employment_type and profile.employment_type.value == "student")
        age = profile.age.value if profile.age else None
        is_underage_for_loan = bool(age is not None and age < 21)

        # In the Indian financial market, personal loans require age 21+ and regular salary slips.
        # Students / under-21 individuals should never be prompted for unsecured loan amounts.
        if is_student or is_underage_for_loan:
            is_loan = False
            is_card = True
        else:
            # Only trigger loan questions if the user explicitly chose personal_loan,
            # or if 'both' was selected and they already provided a loan amount.
            is_loan = (profile.preferred_product == "personal_loan") or (
                profile.preferred_product == "both" and profile.loan_preferences.requested_amount is not None
            )
            is_card = profile.preferred_product in ("credit_card", "both")

        # 1. Monthly income
        if not profile.monthly_income or not profile.monthly_income.value:
            if is_student:
                questions.append(
                    ClarificationQuestion(
                        field="monthly_income",
                        question="Do you receive any monthly pocket allowance or internship stipend?",
                        reason="Helps identify whether you qualify for student cards or FD-backed credit-builder cards.",
                        options=["No Income / Allowance Only", "Under ₹15,000 (Stipend)", "₹15,000 - ₹30,000", "Looking for FD-backed card"]
                    )
                )
            else:
                questions.append(
                    ClarificationQuestion(
                        field="monthly_income",
                        question="What is your approximate monthly take-home income?",
                        reason="Monthly income is required by lenders and card issuers to evaluate credit eligibility.",
                        options=["₹35,000 - ₹50,000", "₹50,000 - ₹1,00,000", "₹1,00,000 - ₹2,00,000", "₹2,00,000+"]
                    )
                )

        # 2. Loan-specific high materiality fields (only when user actively seeks loans)
        if is_loan and len(questions) < 3:
            if not profile.loan_preferences.requested_amount:
                questions.append(
                    ClarificationQuestion(
                        field="requested_amount",
                        question="How much loan amount do you need to borrow?",
                        reason="Requested principal determines EMI calculations and lender borrowing limits.",
                        options=["₹1,00,000", "₹3,00,000", "₹5,00,000", "₹10,00,000"]
                    )
                )
            if not profile.loan_preferences.requested_tenure_months and len(questions) < 3:
                questions.append(
                    ClarificationQuestion(
                        field="requested_tenure_months",
                        question="Over what duration (tenure) would you prefer to repay the loan?",
                        reason="Tenure directly determines your monthly EMI and total interest payable.",
                        options=["12 Months (1 Year)", "24 Months (2 Years)", "36 Months (3 Years)", "60 Months (5 Years)"]
                    )
                )

        # 3. Credit score (useful for both, especially loan APR and premium cards)
        if len(questions) < 3 and (not profile.credit_score or not profile.credit_score.value):
            questions.append(
                ClarificationQuestion(
                    field="credit_score",
                    question="What is your estimated CIBIL / Credit Score?",
                    reason="Credit score affects loan interest rate tiers and credit card approval criteria.",
                    options=["Above 750 (Excellent)", "700 - 750 (Good)", "650 - 700 (Fair)", "New to Credit / No Score"]
                )
            )

        # 4. Card-specific spending clarification if spending is completely zero
        if is_card and len(questions) < 3 and profile.spending.total_monthly_spend == 0:
            questions.append(
                ClarificationQuestion(
                    field="spending_focus",
                    question="Where do you spend the most each month?",
                    reason="Knowing your primary spending category helps match cards with 5x-10x accelerated rewards.",
                    options=["Online Shopping (Amazon, Flipkart)", "Food & Groceries (Swiggy, Zomato)", "Travel & Commute", "Recharges & Utilities"]
                )
            )

        # Profile is considered complete if no high-materiality questions remain
        profile_complete = len(questions) == 0
        profile.is_complete = profile_complete
        profile.missing_information = [q.field for q in questions]

        return ClarificationResponse(
            profile_complete=profile_complete,
            questions=questions[:3]  # Enforce at most 3 questions
        )
