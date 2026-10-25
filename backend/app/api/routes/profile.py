"""
Profile API routes:
- POST /api/v1/profile/parse
- POST /api/v1/profile/chat
- GET /api/v1/profile/{profile_id}
- PATCH /api/v1/profile/{profile_id}
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models import UserProfile, ConversationMessage
from backend.app.schemas.profile import (
    ProfileParseRequest,
    ProfileChatRequest,
    ProfileUpdateRequest,
    ProfileResponse,
    FinancialProfile,
)
from backend.app.services.profile_parser import ProfileParser
from backend.app.services.profile_clarifier import ProfileClarifier

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/parse", response_model=ProfileResponse)
async def parse_profile_endpoint(
    req: ProfileParseRequest,
    db: Session = Depends(get_db)
):
    parser = ProfileParser()
    clarifier = ProfileClarifier()

    # Parse message to profile
    profile = await parser.parse_profile(
        message=req.message,
        category=req.category
    )

    clarifications = clarifier.evaluate(profile)

    # Create UserProfile in DB
    user_profile = UserProfile(
        session_id=req.session_id,
        profile_json=profile.model_dump(),
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user_profile)
    db.flush()

    # Store user message
    msg = ConversationMessage(
        profile_id=user_profile.id,
        role="user",
        content=req.message,
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg)
    db.commit()
    db.refresh(user_profile)

    return ProfileResponse(
        id=user_profile.id,
        session_id=user_profile.session_id,
        profile=profile,
        clarifications=clarifications.questions,
        version=user_profile.version,
        created_at=user_profile.created_at.isoformat(),
        updated_at=user_profile.updated_at.isoformat()
    )


@router.post("/chat", response_model=ProfileResponse)
async def chat_profile_endpoint(
    req: ProfileChatRequest,
    db: Session = Depends(get_db)
):
    user_profile = db.query(UserProfile).filter(UserProfile.id == req.profile_id).first()
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID '{req.profile_id}' not found."
        )

    current_profile = FinancialProfile(**user_profile.profile_json)
    parser = ProfileParser()
    clarifier = ProfileClarifier()

    # Merge new information
    updated_profile = await parser.parse_profile(
        message=req.message,
        current_profile=current_profile
    )
    clarifications = clarifier.evaluate(updated_profile)

    # Save to DB
    user_profile.profile_json = updated_profile.model_dump()
    user_profile.version += 1
    user_profile.updated_at = datetime.now(timezone.utc)

    msg = ConversationMessage(
        profile_id=user_profile.id,
        role="user",
        content=req.message,
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg)
    db.commit()
    db.refresh(user_profile)

    return ProfileResponse(
        id=user_profile.id,
        session_id=user_profile.session_id,
        profile=updated_profile,
        clarifications=clarifications.questions,
        version=user_profile.version,
        created_at=user_profile.created_at.isoformat(),
        updated_at=user_profile.updated_at.isoformat()
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile_endpoint(
    profile_id: str,
    db: Session = Depends(get_db)
):
    user_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID '{profile_id}' not found."
        )

    profile = FinancialProfile(**user_profile.profile_json)
    clarifier = ProfileClarifier()
    clarifications = clarifier.evaluate(profile)

    return ProfileResponse(
        id=user_profile.id,
        session_id=user_profile.session_id,
        profile=profile,
        clarifications=clarifications.questions,
        version=user_profile.version,
        created_at=user_profile.created_at.isoformat(),
        updated_at=user_profile.updated_at.isoformat()
    )


@router.patch("/{profile_id}", response_model=ProfileResponse)
def update_profile_endpoint(
    profile_id: str,
    req: ProfileUpdateRequest,
    db: Session = Depends(get_db)
):
    user_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID '{profile_id}' not found."
        )

    profile_dict = dict(user_profile.profile_json)
    
    if req.monthly_income is not None:
        profile_dict["monthly_income"] = {"value": req.monthly_income, "source": "confirmed", "confidence": 1.0}
    if req.employment_type is not None:
        profile_dict["employment_type"] = {"value": req.employment_type, "source": "confirmed", "confidence": 1.0}
    if req.credit_score is not None:
        profile_dict["credit_score"] = {"value": req.credit_score, "source": "confirmed", "confidence": 1.0}
    if req.existing_monthly_emi is not None:
        profile_dict["existing_monthly_emi"] = {"value": req.existing_monthly_emi, "source": "confirmed", "confidence": 1.0}
    if req.city is not None:
        profile_dict["city"] = {"value": req.city, "source": "confirmed", "confidence": 1.0}
    if req.preferred_product is not None:
        profile_dict["preferred_product"] = req.preferred_product
    if req.spending is not None:
        profile_dict["spending"] = {**profile_dict.get("spending", {}), **req.spending}
    if req.card_preferences is not None:
        profile_dict["card_preferences"] = {**profile_dict.get("card_preferences", {}), **req.card_preferences}
    if req.loan_preferences is not None:
        profile_dict["loan_preferences"] = {**profile_dict.get("loan_preferences", {}), **req.loan_preferences}

    profile = FinancialProfile(**profile_dict)
    clarifier = ProfileClarifier()
    clarifications = clarifier.evaluate(profile)

    user_profile.profile_json = profile.model_dump()
    user_profile.version += 1
    user_profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_profile)

    return ProfileResponse(
        id=user_profile.id,
        session_id=user_profile.session_id,
        profile=profile,
        clarifications=clarifications.questions,
        version=user_profile.version,
        created_at=user_profile.created_at.isoformat(),
        updated_at=user_profile.updated_at.isoformat()
    )
