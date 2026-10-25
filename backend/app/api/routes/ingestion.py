"""
Ingestion & Admin API routes:
- POST /api/v1/products/ingest
- GET /api/v1/ingestion/status
- GET /api/v1/ingestion/sources
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models import IngestionRun, Product, ProductSource, ProductFieldEvidence
from backend.app.services.source_discovery import OFFICIAL_SOURCES
from backend.app.services.website_fetcher import WebsiteFetcher
from backend.app.services.page_parser import PageParser
from backend.app.services.product_extractor import ProductExtractor
from backend.app.services.product_verifier import ProductVerifier
from backend.app.core.config import settings

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.get("/sources")
def get_sources_endpoint():
    return OFFICIAL_SOURCES


@router.get("/status")
def get_ingestion_status(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    runs = db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit).all()
    products_count = db.query(Product).count()
    verified_count = db.query(Product).filter(Product.data_quality_status == "verified").count()
    partially_count = db.query(Product).filter(Product.data_quality_status == "partially_verified").count()
    stale_count = db.query(Product).filter(Product.data_quality_status == "stale").count()
    conflict_count = db.query(Product).filter(Product.data_quality_status == "conflicting_sources").count()

    run_list = []
    for r in runs:
        run_list.append({
            "id": r.id,
            "source_identifier": r.source_identifier,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else "",
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "pages_fetched": r.pages_fetched,
            "products_extracted": r.products_extracted,
            "products_verified": r.products_verified,
            "error_details": r.error_details
        })

    return {
        "stats": {
            "total_products": products_count,
            "verified": verified_count,
            "partially_verified": partially_count,
            "stale": stale_count,
            "conflicting_sources": conflict_count,
            "configured_sources": len(OFFICIAL_SOURCES)
        },
        "recent_runs": run_list
    }


@router.post("/run")
async def trigger_ingestion_run(
    source_id: Optional[str] = Query(None, description="Specific source to ingest, or None for all"),
    force_fixture: bool = Query(True, description="Use verified fixtures when live bank anti-bot activates"),
    db: Session = Depends(get_db)
):
    sources_to_run = OFFICIAL_SOURCES
    if source_id:
        sources_to_run = [s for s in OFFICIAL_SOURCES if s["source_id"] == source_id]
        if not sources_to_run:
            raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")

    fetcher = WebsiteFetcher()
    parser = PageParser()
    extractor = ProductExtractor()
    verifier = ProductVerifier()

    run = IngestionRun(
        source_identifier=source_id or "all_official_sources",
        status="running",
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    db.commit()

    pages_fetched = 0
    prods_created = 0
    prods_verified = 0

    try:
        for src in sources_to_run:
            fetch_res = await fetcher.fetch_page(
                url=src["url"],
                fixture_path=src.get("fixture_path"),
                force_fixture=force_fixture
            )
            pages_fetched += 1

            parse_res = parser.parse_html(fetch_res["html_content"])
            terms_dict, raw_evidences = extractor.extract_product_from_text(
                parse_res["clean_text"],
                src
            )

            status, verified_evs = verifier.verify_product(
                {"structured_terms": terms_dict},
                raw_evidences,
                {**src, "fetched_at": fetch_res["fetched_at"]}
            )

            # Check if product already exists
            existing_product = db.query(Product).filter(Product.product_name == src["product_name"]).first()
            if existing_product:
                product = existing_product
                product.structured_terms = terms_dict
                product.data_quality_status = status
                product.last_verified_at = datetime.now(timezone.utc)
            else:
                product = Product(
                    product_name=src["product_name"],
                    issuer=src["institution"],
                    product_type=src["product_type"],
                    canonical_url=src["url"],
                    structured_terms=terms_dict,
                    data_quality_status=status,
                    last_verified_at=datetime.now(timezone.utc),
                    active=True
                )
                db.add(product)
                db.flush()

            # Clear old evidences for this product and update
            db.query(ProductFieldEvidence).filter(ProductFieldEvidence.product_id == product.id).delete()
            for ev in verified_evs:
                db_ev = ProductFieldEvidence(
                    product_id=product.id,
                    field_name=ev["field_name"],
                    extracted_value=ev.get("extracted_value"),
                    normalized_value=ev.get("normalized_value"),
                    evidence_excerpt=ev.get("evidence_excerpt", ""),
                    source_url=ev.get("source_url", src["url"]),
                    verification_status=ev.get("verification_status", "verified"),
                    confidence=ev.get("confidence", 1.0),
                    verified_at=datetime.now(timezone.utc)
                )
                db.add(db_ev)

            prods_created += 1
            if status == "verified":
                prods_verified += 1

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.pages_fetched = pages_fetched
        run.products_extracted = prods_created
        run.products_verified = prods_verified
        db.commit()

        return {
            "run_id": run.id,
            "status": "completed",
            "pages_fetched": pages_fetched,
            "products_extracted": prods_created,
            "products_verified": prods_verified
        }
    except Exception as e:
        db.rollback()
        run.status = "failed"
        run.error_details = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
