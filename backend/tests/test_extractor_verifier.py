"""
Unit tests for Product Extractor and Independent Verification Engine.
"""
from datetime import datetime, timezone, timedelta
from backend.app.services.product_extractor import ProductExtractor
from backend.app.services.product_verifier import ProductVerifier


def test_extract_hdfc_millennia_card():
    extractor = ProductExtractor()
    with open("data/fixtures/hdfc_millennia.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    metadata = {
        "product_name": "HDFC Bank Millennia Credit Card",
        "institution": "HDFC Bank",
        "product_type": "credit_card",
        "url": "https://www.hdfcbank.com/personal/pay/cards/credit-cards/millennia-cards"
    }
    
    terms, evidences = extractor.extract_product_from_text(html, metadata)
    assert terms["joining_fee"] == 1000.0
    assert terms["annual_fee"] == 1000.0
    assert terms["fee_waiver_spend_threshold"] == 100000.0
    assert terms["monthly_reward_cap"] == 1000.0
    assert len(evidences) >= 3

    # Now verify with ProductVerifier
    verifier = ProductVerifier()
    status, verified_evs = verifier.verify_product(
        {"structured_terms": terms},
        evidences,
        {**metadata, "fetched_at": datetime.now(timezone.utc).isoformat()}
    )
    assert status == "verified"
    for ev in verified_evs:
        assert ev["verification_status"] in ("verified", "partially_verified")


def test_extract_hdfc_personal_loan():
    extractor = ProductExtractor()
    with open("data/fixtures/hdfc_personal_loan.html", "r", encoding="utf-8") as f:
        html = f.read()

    metadata = {
        "product_name": "HDFC Bank Personal Loan",
        "institution": "HDFC Bank",
        "product_type": "personal_loan",
        "url": "https://www.hdfcbank.com/personal/borrow/popular-loans/personal-loan"
    }

    terms, evidences = extractor.extract_product_from_text(html, metadata)
    assert terms["min_amount"] == 50000.0
    assert terms["max_amount"] == 4000000.0
    assert terms["interest_rate_min"] == 10.75
    assert terms["interest_rate_max"] == 21.0
    assert terms["min_tenure_months"] == 12
    assert terms["max_tenure_months"] == 60
    assert terms["processing_fee_pct"] == 2.50

    verifier = ProductVerifier()
    status, verified_evs = verifier.verify_product(
        {"structured_terms": terms},
        evidences,
        {**metadata, "fetched_at": datetime.now(timezone.utc).isoformat()}
    )
    assert status == "verified"


def test_verifier_detects_consistency_errors():
    verifier = ProductVerifier()
    inconsistent_terms = {
        "min_amount": 500000.0,
        "max_amount": 100000.0,  # min > max!
        "interest_rate_min": 15.0,
        "interest_rate_max": 10.0  # min > max!
    }
    status, _ = verifier.verify_product(
        {"structured_terms": inconsistent_terms},
        [],
        {"product_type": "personal_loan", "url": "https://www.hdfcbank.com"}
    )
    assert status == "conflicting_sources"


def test_verifier_flags_stale_data():
    verifier = ProductVerifier()
    old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    status, verified_evs = verifier.verify_product(
        {"structured_terms": {"annual_fee": 500.0}},
        [{"field_name": "annual_fee", "normalized_value": 500.0, "evidence_excerpt": "Annual fee is 500"}],
        {"product_type": "credit_card", "url": "https://www.hdfcbank.com", "fetched_at": old_date}
    )
    assert status == "stale"
    assert verified_evs[0]["verification_status"] == "stale"


def test_verifier_rejects_unwhitelisted_domain():
    verifier = ProductVerifier()
    status, verified_evs = verifier.verify_product(
        {"structured_terms": {"annual_fee": 500.0}},
        [{"field_name": "annual_fee", "normalized_value": 500.0, "evidence_excerpt": "Annual fee is 500"}],
        {"product_type": "credit_card", "url": "https://suspicious-unauthorized-site.com"}
    )
    assert status == "unverified"
    assert verified_evs[0]["verification_status"] == "unverified"
