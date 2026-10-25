"""
Curated source registry of official Indian financial institution sources.
"""
from typing import List, Dict, Any


OFFICIAL_SOURCES: List[Dict[str, Any]] = [
    {
        "source_id": "hdfc_millennia_card",
        "institution": "HDFC Bank",
        "product_name": "HDFC Millennia Credit Card",
        "product_type": "credit_card",
        "url": "https://www.hdfcbank.com/personal/pay/cards/credit-cards/millennia-cards",
        "domain": "hdfcbank.com",
        "fixture_path": "data/fixtures/hdfc_millennia.html",
        "enabled": True,
    },
    {
        "source_id": "sbi_simplyclick_card",
        "institution": "SBI Card",
        "product_name": "SBI SimplyCLICK Credit Card",
        "product_type": "credit_card",
        "url": "https://www.sbicard.com/en/personal/credit-cards/rewards/simplyclick-sbi-card.page",
        "domain": "sbicard.com",
        "fixture_path": "data/fixtures/sbi_simplyclick.html",
        "enabled": True,
    },
    {
        "source_id": "icici_amazon_pay_card",
        "institution": "ICICI Bank",
        "product_name": "Amazon Pay ICICI Bank Credit Card",
        "product_type": "credit_card",
        "url": "https://www.icicibank.com/personal-banking/cards/credit-cards/amazon-pay-credit-card",
        "domain": "icicibank.com",
        "fixture_path": "data/fixtures/icici_amazon_pay.html",
        "enabled": True,
    },
    {
        "source_id": "hdfc_personal_loan",
        "institution": "HDFC Bank",
        "product_name": "HDFC Bank Personal Loan",
        "product_type": "personal_loan",
        "url": "https://www.hdfcbank.com/personal/borrow/popular-loans/personal-loan",
        "domain": "hdfcbank.com",
        "fixture_path": "data/fixtures/hdfc_personal_loan.html",
        "enabled": True,
    },
    {
        "source_id": "sbi_personal_loan",
        "institution": "State Bank of India",
        "product_name": "SBI Xpress Credit Personal Loan",
        "product_type": "personal_loan",
        "url": "https://sbi.co.in/web/personal-banking/loans/personal-loans/xpress-credit",
        "domain": "sbi.co.in",
        "fixture_path": "data/fixtures/sbi_personal_loan.html",
        "enabled": True,
    },
    {
        "source_id": "icici_personal_loan",
        "institution": "ICICI Bank",
        "product_name": "ICICI Bank Personal Loan",
        "product_type": "personal_loan",
        "url": "https://www.icicibank.com/personal-banking/loans/personal-loan",
        "domain": "icicibank.com",
        "fixture_path": "data/fixtures/icici_personal_loan.html",
        "enabled": True,
    },
]


def get_official_sources(category: str | None = None) -> List[Dict[str, Any]]:
    sources = [s for s in OFFICIAL_SOURCES if s["enabled"]]
    if category and category != "both":
        sources = [s for s in sources if s["product_type"] == category]
    return sources


def get_allowed_domains() -> List[str]:
    return list(set(s["domain"] for s in OFFICIAL_SOURCES))
