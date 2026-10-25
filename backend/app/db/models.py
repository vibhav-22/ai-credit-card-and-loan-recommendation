"""
SQLAlchemy models for UserProfile, Products, Evidence, Ingestion, and Recommendations.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(64), index=True, nullable=True)
    profile_json = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    messages = relationship("ConversationMessage", back_populates="profile", cascade="all, delete-orphan")
    recommendation_runs = relationship("RecommendationRun", back_populates="profile", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    profile = relationship("UserProfile", back_populates="messages")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_name = Column(String(255), nullable=False, index=True)
    issuer = Column(String(120), nullable=False, index=True)  # e.g. "HDFC Bank", "SBI Card"
    product_type = Column(String(50), nullable=False, index=True)  # "credit_card", "personal_loan"
    canonical_url = Column(String(512), nullable=False)
    structured_terms = Column(JSON, nullable=False, default=dict)
    data_quality_status = Column(String(50), default="verified", nullable=False)  # "verified", "partially_verified", "stale"
    last_verified_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    sources = relationship("ProductSource", back_populates="product", cascade="all, delete-orphan")
    field_evidences = relationship("ProductFieldEvidence", back_populates="product", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="product")

    __table_args__ = (
        Index("idx_product_type_issuer", "product_type", "issuer"),
    )


class ProductSource(Base):
    __tablename__ = "product_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    source_url = Column(String(512), nullable=False)
    domain = Column(String(120), nullable=False, index=True)
    source_type = Column(String(50), default="official_page", nullable=False)
    fetch_timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    publication_date = Column(String(50), nullable=True)
    content_hash = Column(String(64), nullable=False)
    http_status = Column(Integer, default=200, nullable=False)
    extracted_text_ref = Column(Text, nullable=True)

    product = relationship("Product", back_populates="sources")


class ProductFieldEvidence(Base):
    __tablename__ = "product_field_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)  # e.g. "annual_fee", "interest_rate_min"
    extracted_value = Column(JSON, nullable=True)
    normalized_value = Column(JSON, nullable=True)
    evidence_excerpt = Column(Text, nullable=False)
    source_url = Column(String(512), nullable=False)
    verification_status = Column(String(50), default="verified", nullable=False)  # "verified", "partially_verified", "conflicting_sources", "stale", "unverified"
    confidence = Column(Float, default=1.0, nullable=False)
    verified_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    product = relationship("Product", back_populates="field_evidences")

    __table_args__ = (
        Index("idx_product_field", "product_id", "field_name"),
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_identifier = Column(String(120), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running", nullable=False)  # "running", "completed", "failed"
    error_details = Column(Text, nullable=True)
    pages_fetched = Column(Integer, default=0, nullable=False)
    products_extracted = Column(Integer, default=0, nullable=False)
    products_verified = Column(Integer, default=0, nullable=False)


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_category = Column(String(50), nullable=False)  # "credit_card", "personal_loan"
    profile_snapshot = Column(JSON, nullable=False)
    matching_config_version = Column(String(50), default="v1.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    profile = relationship("UserProfile", back_populates="recommendation_runs")
    recommendations = relationship("Recommendation", back_populates="run", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recommendation_run_id = Column(String(36), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False)  # 0 to 100
    eligibility_status = Column(String(50), nullable=False)  # "meets_published_criteria", "may_meet_criteria", "does_not_meet_published_criteria"
    score_breakdown = Column(JSON, nullable=False, default=dict)
    explanation = Column(JSON, nullable=False, default=dict)
    calculation_assumptions = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    run = relationship("RecommendationRun", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")
