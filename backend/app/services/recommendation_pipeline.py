"""
Unified Recommendation Pipeline:
Orchestrates profile loading, product discovery, deterministic matching,
LLM-based personalized explanations, and result persistence.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models import UserProfile, Product, RecommendationRun, Recommendation, generate_uuid
from backend.app.db.seed import seed_initial_products_if_empty
from backend.app.schemas.profile import FinancialProfile
from backend.app.schemas.recommendation import (
    RecommendationRunResponse,
    RecommendationItem,
    ScoreBreakdown,
    FinancialCalculations,
    ExplanationOut,
)
from backend.app.schemas.product import ProductOut
from backend.app.services.matching_engine import MatchingEngine
from backend.app.services.recommendation_explainer import RecommendationExplainer
from backend.app.core.logging import logger


class RecommendationPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.matching_engine = MatchingEngine()
        self.explainer = RecommendationExplainer()

    async def run(
        self,
        profile_id: str,
        category: Optional[str] = None
    ) -> RecommendationRunResponse:
        # Ensure products exist in DB
        await seed_initial_products_if_empty(self.db)

        # 1. Load User Profile
        user_profile = self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not user_profile:
            raise ValueError(f"User profile with id '{profile_id}' not found.")

        profile_data = FinancialProfile(**user_profile.profile_json)
        selected_category = category or profile_data.preferred_product

        # 2. Query Active Products
        query = self.db.query(Product).filter(Product.active == True)
        if selected_category and selected_category != "both":
            query = query.filter(Product.product_type == selected_category)
        db_products = query.all()

        products_list = []
        for p in db_products:
            p_dict = {
                "id": p.id,
                "product_name": p.product_name,
                "issuer": p.issuer,
                "product_type": p.product_type,
                "canonical_url": p.canonical_url,
                "structured_terms": p.structured_terms,
                "data_quality_status": p.data_quality_status,
                "last_verified_at": p.last_verified_at.isoformat() if p.last_verified_at else None,
                "active": p.active,
            }
            products_list.append(p_dict)

        # 3. Deterministic Matching & Ranking
        scored_products = self.matching_engine.evaluate_and_rank_products(
            profile=profile_data,
            products=products_list,
            category=selected_category
        )

        # 4. Generate Explanations for Ranked Products
        recommendation_items: List[RecommendationItem] = []
        
        # Create DB RecommendationRun
        rec_run = RecommendationRun(
            profile_id=profile_id,
            product_category=selected_category,
            profile_snapshot=profile_data.model_dump(),
            matching_config_version="v1.0",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(rec_run)
        self.db.flush()

        for sp in scored_products:
            p_dict = sp["product"]
            # Call explainer
            explanation = await self.explainer.explain_recommendation(
                profile=profile_data,
                product=p_dict,
                scored_data=sp
            )

            # Persist Recommendation entry
            rec_id = generate_uuid()
            rec_entry = Recommendation(
                id=rec_id,
                recommendation_run_id=rec_run.id,
                product_id=p_dict["id"],
                match_score=sp["match_score"],
                eligibility_status=sp["eligibility_status"],
                score_breakdown=sp["score_breakdown"],
                explanation=explanation.model_dump(),
                calculation_assumptions=sp["calculation_assumptions"],
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(rec_entry)

            prod_out = ProductOut(
                id=p_dict["id"],
                product_name=p_dict["product_name"],
                issuer=p_dict["issuer"],
                product_type=p_dict["product_type"],
                canonical_url=p_dict["canonical_url"],
                structured_terms=p_dict["structured_terms"],
                data_quality_status=p_dict["data_quality_status"],
                last_verified_at=p_dict["last_verified_at"] or "",
                active=p_dict["active"]
            )

            item = RecommendationItem(
                id=rec_entry.id,
                product_id=p_dict["id"],
                product=prod_out,
                match_score=sp["match_score"],
                eligibility_status=sp["eligibility_status"],
                score_breakdown=ScoreBreakdown(**sp["score_breakdown"]),
                financial_calculations=FinancialCalculations(**sp["financial_calculations"]),
                explanation=explanation,
                matched_preferences=sp["matched_preferences"],
                mismatches=sp["mismatches"],
                unknowns=sp["unknowns"],
                calculation_assumptions=sp["calculation_assumptions"]
            )
            recommendation_items.append(item)

        self.db.commit()

        return RecommendationRunResponse(
            run_id=rec_run.id,
            profile_id=profile_id,
            product_category=selected_category,
            profile_summary=profile_data,
            recommendations=recommendation_items,
            total_evaluated=len(products_list),
            created_at=rec_run.created_at.isoformat()
        )
