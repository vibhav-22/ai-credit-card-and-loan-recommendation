"""
Recommendation API routes:
- POST /api/v1/recommendations
- GET /api/v1/recommendations/{run_id}
- POST /api/v1/recommendations/compare
"""
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models import RecommendationRun, Recommendation, Product, UserProfile
from backend.app.schemas.recommendation import (
    RecommendationRunResponse,
    RecommendationItem,
    ComparisonRequest,
    ComparisonResponse,
    ComparisonItem,
    ScoreBreakdown,
    FinancialCalculations,
    ExplanationOut,
)
from backend.app.schemas.product import ProductOut, CreditCardTerms, LoanTerms
from backend.app.schemas.profile import FinancialProfile
from backend.app.services.recommendation_pipeline import RecommendationPipeline
from backend.app.services.card_value_calculator import calculate_credit_card_annual_value
from backend.app.services.loan_calculator import calculate_loan_range_metrics

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class GenerateRecommendationRequest(BaseModel):
    profile_id: str
    category: Optional[str] = None


@router.post("", response_model=RecommendationRunResponse)
async def create_recommendation_run(
    req: GenerateRecommendationRequest,
    db: Session = Depends(get_db)
):
    pipeline = RecommendationPipeline(db)
    try:
        response = await pipeline.run(
            profile_id=req.profile_id,
            category=req.category
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pipeline error: {str(e)}")


@router.get("/{run_id}", response_model=RecommendationRunResponse)
def get_recommendation_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    rec_run = db.query(RecommendationRun).filter(RecommendationRun.id == run_id).first()
    if not rec_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation run '{run_id}' not found."
        )

    recommendations = db.query(Recommendation).filter(Recommendation.recommendation_run_id == run_id).all()
    items: List[RecommendationItem] = []

    for r in recommendations:
        p = db.query(Product).filter(Product.id == r.product_id).first()
        if not p:
            continue
        prod_out = ProductOut(
            id=p.id,
            product_name=p.product_name,
            issuer=p.issuer,
            product_type=p.product_type,
            canonical_url=p.canonical_url,
            structured_terms=p.structured_terms,
            data_quality_status=p.data_quality_status,
            last_verified_at=p.last_verified_at.isoformat() if p.last_verified_at else "",
            active=p.active
        )
        item = RecommendationItem(
            id=r.id,
            product_id=r.product_id,
            product=prod_out,
            match_score=r.match_score,
            eligibility_status=r.eligibility_status,
            score_breakdown=ScoreBreakdown(**r.score_breakdown),
            financial_calculations=FinancialCalculations(**(r.score_breakdown.get("financial_calculations") or {})),
            explanation=ExplanationOut(**r.explanation),
            calculation_assumptions=r.calculation_assumptions
        )
        items.append(item)

    items.sort(key=lambda x: x.match_score, reverse=True)

    profile_summary = FinancialProfile(**rec_run.profile_snapshot)

    return RecommendationRunResponse(
        run_id=rec_run.id,
        profile_id=rec_run.profile_id,
        product_category=rec_run.product_category,
        profile_summary=profile_summary,
        recommendations=items,
        total_evaluated=len(items),
        created_at=rec_run.created_at.isoformat()
    )


@router.post("/compare", response_model=ComparisonResponse)
def compare_products_endpoint(
    req: ComparisonRequest,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(Product.id.in_(req.product_ids)).all()
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="None of the specified products were found.")

    category = products[0].product_type

    # Optional profile context
    profile: Optional[FinancialProfile] = None
    if req.profile_id:
        user_prof = db.query(UserProfile).filter(UserProfile.id == req.profile_id).first()
        if user_prof:
            profile = FinancialProfile(**user_prof.profile_json)

    comparison_items: List[ComparisonItem] = []

    for p in products:
        terms = p.structured_terms
        fin_calc = None
        pros = []
        cons = []

        if p.product_type == "credit_card":
            card_terms = CreditCardTerms(**terms)
            if profile:
                val = calculate_credit_card_annual_value(card_terms, profile.spending)
                fin_calc = FinancialCalculations(
                    estimated_annual_spend=val["estimated_annual_spend"],
                    estimated_annual_rewards=val["estimated_annual_rewards"],
                    annual_fee_effective=val["annual_fee_effective"],
                    fee_waived=val["fee_waived"],
                    net_annual_benefit=val["net_annual_benefit"],
                    first_year_net_benefit=val["first_year_net_benefit"],
                    reward_breakdown_by_category=val["reward_breakdown_by_category"]
                )

            if card_terms.annual_fee == 0:
                pros.append("Lifetime Free / No Annual Fee")
            elif card_terms.fee_waiver_spend_threshold:
                pros.append(f"Annual fee waiver on ₹{card_terms.fee_waiver_spend_threshold:,.0f} spend")

            if (card_terms.online_shopping_cashback_pct or 0) >= 3.0:
                pros.append(f"Accelerated {card_terms.online_shopping_cashback_pct}% cashback on online shopping")
            if card_terms.monthly_reward_cap:
                cons.append(f"Monthly reward cap of ₹{card_terms.monthly_reward_cap:,.0f}")
            if card_terms.annual_fee > 0:
                cons.append(f"₹{card_terms.annual_fee:,.0f} annual fee if waiver spend is not met")

        else:
            loan_terms = LoanTerms(**terms)
            amt = profile.loan_preferences.requested_amount if profile and profile.loan_preferences.requested_amount else 300000.0
            tenure = profile.loan_preferences.requested_tenure_months if profile and profile.loan_preferences.requested_tenure_months else 36

            metrics = calculate_loan_range_metrics(
                principal=amt,
                interest_rate_min=loan_terms.interest_rate_min,
                interest_rate_max=loan_terms.interest_rate_max,
                tenure_months=tenure,
                processing_fee_pct=loan_terms.processing_fee_pct,
                min_processing_fee=loan_terms.processing_fee_min,
                max_processing_fee=loan_terms.processing_fee_max
            )
            fin_calc = FinancialCalculations(
                requested_amount=amt,
                requested_tenure_months=tenure,
                estimated_emi_min=metrics["estimated_emi_min"],
                estimated_emi_max=metrics["estimated_emi_max"],
                total_repayment_min=metrics["total_repayment_min"],
                total_repayment_max=metrics["total_repayment_max"],
                total_interest_min=metrics["total_interest_min"],
                total_interest_max=metrics["total_interest_max"],
                estimated_processing_fee=metrics["estimated_processing_fee"],
                is_zero_interest=metrics["is_zero_interest"]
            )

            pros.append(f"Starting interest rate from {loan_terms.interest_rate_min:.2f}% p.a.")
            pros.append(f"Borrow up to ₹{loan_terms.max_amount:,.0f} for up to {loan_terms.max_tenure_months} months")
            if loan_terms.processing_fee_pct <= 1.5:
                pros.append(f"Low processing charge ({loan_terms.processing_fee_pct:.1f}%)")
            else:
                cons.append(f"Processing fee up to {loan_terms.processing_fee_pct:.1f}% + GST")
            if loan_terms.interest_rate_max > 18.0:
                cons.append(f"Upper rate bracket reaches up to {loan_terms.interest_rate_max:.2f}% p.a.")

        prod_out = ProductOut(
            id=p.id,
            product_name=p.product_name,
            issuer=p.issuer,
            product_type=p.product_type,
            canonical_url=p.canonical_url,
            structured_terms=p.structured_terms,
            data_quality_status=p.data_quality_status,
            last_verified_at=p.last_verified_at.isoformat() if p.last_verified_at else "",
            active=p.active
        )

        comparison_items.append(
            ComparisonItem(
                product=prod_out,
                financial_calculations=fin_calc,
                pros=pros,
                cons=cons
            )
        )

    return ComparisonResponse(
        category=category,
        products=comparison_items
    )
