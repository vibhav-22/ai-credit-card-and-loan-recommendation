"""
End-to-End API endpoint integration tests using FastAPI TestClient.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_full_recommendation_flow():
    # 1. Parse natural language profile
    user_msg = (
        "I'm 26, working in Bengaluru, earning ₹75,000 monthly in IT. "
        "I spend ₹10,000 on food/dining and ₹8,000 on online shopping. "
        "Looking for a cashback credit card with low annual fee. My credit score is 770."
    )
    parse_resp = client.post("/api/v1/profile/parse", json={"message": user_msg, "category": "credit_card"})
    assert parse_resp.status_code == 200
    profile_data = parse_resp.json()
    profile_id = profile_data["id"]
    assert profile_data["profile"]["monthly_income"]["value"] == 75000.0
    assert profile_data["profile"]["credit_score"]["value"] == 770

    # 2. Add conversational follow-up
    chat_resp = client.post("/api/v1/profile/chat", json={
        "profile_id": profile_id,
        "message": "I also have an HDFC salary account."
    })
    assert chat_resp.status_code == 200
    updated = chat_resp.json()
    assert updated["version"] == 2

    # 3. Generate Recommendations
    rec_resp = client.post("/api/v1/recommendations", json={
        "profile_id": profile_id,
        "category": "credit_card"
    })
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert len(rec_data["recommendations"]) > 0
    top_rec = rec_data["recommendations"][0]
    assert "match_score" in top_rec
    assert "score_breakdown" in top_rec
    assert "financial_calculations" in top_rec
    assert "explanation" in top_rec
    assert top_rec["explanation"]["why_it_matches"]

    # 4. Compare products
    prod_ids = [r["product_id"] for r in rec_data["recommendations"][:2]]
    if len(prod_ids) >= 2:
        comp_resp = client.post("/api/v1/recommendations/compare", json={
            "product_ids": prod_ids,
            "profile_id": profile_id
        })
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert len(comp_data["products"]) == 2


def test_loan_recommendation_flow():
    user_msg = "Need a personal loan of ₹4 lakh for 36 months. Salary is ₹60,000/mo."
    parse_resp = client.post("/api/v1/profile/parse", json={"message": user_msg, "category": "personal_loan"})
    assert parse_resp.status_code == 200
    profile_id = parse_resp.json()["id"]

    rec_resp = client.post("/api/v1/recommendations", json={
        "profile_id": profile_id,
        "category": "personal_loan"
    })
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert len(rec_data["recommendations"]) > 0
    first_loan = rec_data["recommendations"][0]
    assert first_loan["financial_calculations"]["requested_amount"] == 400000.0
    assert first_loan["financial_calculations"]["requested_tenure_months"] == 36
    assert first_loan["financial_calculations"]["estimated_emi_min"] > 0


def test_products_listing_and_evidence():
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200
    prods = resp.json()
    assert len(prods) >= 3

    p_id = prods[0]["id"]
    detail_resp = client.get(f"/api/v1/products/{p_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "field_evidences" in detail
    assert len(detail["field_evidences"]) > 0


def test_ingestion_status():
    resp = client.get("/api/v1/ingestion/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stats"]["total_products"] > 0
