"""
Products API routes:
- GET /api/v1/products
- GET /api/v1/products/{product_id}
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models import Product, ProductFieldEvidence
from backend.app.db.seed import seed_initial_products_if_empty
from backend.app.schemas.product import ProductOut, FieldEvidenceOut

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductOut])
async def list_products(
    product_type: Optional[str] = Query(None, description="credit_card or personal_loan"),
    issuer: Optional[str] = Query(None, description="Bank or issuer name filter"),
    search: Optional[str] = Query(None, description="Keyword search in name or issuer"),
    db: Session = Depends(get_db)
):
    await seed_initial_products_if_empty(db)
    
    query = db.query(Product).filter(Product.active == True)
    if product_type and product_type != "both":
        query = query.filter(Product.product_type == product_type)
    if issuer:
        query = query.filter(Product.issuer.ilike(f"%{issuer}%"))
    if search:
        query = query.filter(
            (Product.product_name.ilike(f"%{search}%")) | (Product.issuer.ilike(f"%{search}%"))
        )

    products = query.all()
    results = []
    for p in products:
        results.append(
            ProductOut(
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
        )
    return results


@router.get("/{product_id}", response_model=ProductOut)
async def get_product_details(
    product_id: str,
    db: Session = Depends(get_db)
):
    await seed_initial_products_if_empty(db)
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found."
        )

    evidences = db.query(ProductFieldEvidence).filter(ProductFieldEvidence.product_id == p.id).all()
    ev_list = [
        FieldEvidenceOut(
            id=e.id,
            field_name=e.field_name,
            extracted_value=e.extracted_value,
            normalized_value=e.normalized_value,
            evidence_excerpt=e.evidence_excerpt,
            source_url=e.source_url,
            verification_status=e.verification_status,
            confidence=e.confidence,
            verified_at=e.verified_at.isoformat() if e.verified_at else ""
        )
        for e in evidences
    ]

    return ProductOut(
        id=p.id,
        product_name=p.product_name,
        issuer=p.issuer,
        product_type=p.product_type,
        canonical_url=p.canonical_url,
        structured_terms=p.structured_terms,
        data_quality_status=p.data_quality_status,
        last_verified_at=p.last_verified_at.isoformat() if p.last_verified_at else "",
        active=p.active,
        field_evidences=ev_list
    )
