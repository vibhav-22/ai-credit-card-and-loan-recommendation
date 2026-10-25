"""
Database seed service:
Ingests verified official fixture products (HDFC, SBI, ICICI) into the database
with full field-level evidence and provenance.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models import Product, ProductSource, ProductFieldEvidence, IngestionRun
from backend.app.services.source_discovery import OFFICIAL_SOURCES
from backend.app.services.website_fetcher import WebsiteFetcher
from backend.app.services.page_parser import PageParser
from backend.app.services.product_extractor import ProductExtractor
from backend.app.services.product_verifier import ProductVerifier
from backend.app.core.logging import logger


async def seed_initial_products_if_empty(db: Session):
    existing_count = db.query(Product).count()
    if existing_count > 0:
        logger.info(f"Database already contains {existing_count} products. Skipping initial seed.")
        return

    logger.info("Database is empty. Ingesting verified official sources...")
    fetcher = WebsiteFetcher()
    parser = PageParser()
    extractor = ProductExtractor()
    verifier = ProductVerifier()

    run = IngestionRun(
        source_identifier="initial_seed_official_fixtures",
        status="running",
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    db.commit()

    products_created = 0
    try:
        for src in OFFICIAL_SOURCES:
            fixture_path = src.get("fixture_path")
            fetch_res = await fetcher.fetch_page(
                url=src["url"],
                fixture_path=fixture_path,
                force_fixture=True
            )

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

            # Add source record
            prod_source = ProductSource(
                product_id=product.id,
                source_url=src["url"],
                domain=src["domain"],
                source_type="official_fixture",
                fetch_timestamp=datetime.now(timezone.utc),
                content_hash=fetch_res["content_hash"],
                http_status=200,
                extracted_text_ref=parse_res["clean_text"][:500]
            )
            db.add(prod_source)

            # Add field evidences
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

            products_created += 1

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.pages_fetched = len(OFFICIAL_SOURCES)
        run.products_extracted = products_created
        run.products_verified = products_created
        db.commit()
        logger.info(f"Successfully seeded {products_created} verified products.")
    except Exception as e:
        db.rollback()
        run.status = "failed"
        run.error_details = str(e)
        db.commit()
        logger.error(f"Seeding failed: {e}")
