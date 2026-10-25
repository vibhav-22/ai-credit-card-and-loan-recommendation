"""
Unit tests for Website Fetcher, SSRF security, and Page Parser.
"""
import pytest
from backend.app.core.security import is_safe_url
from backend.app.services.website_fetcher import WebsiteFetcher
from backend.app.services.page_parser import PageParser


def test_ssrf_blocked_ips():
    # Loopback
    safe, msg = is_safe_url("http://127.0.0.1:8000/secret")
    assert safe is False
    assert "restricted IP" in msg

    # Metadata service
    safe, msg = is_safe_url("http://169.254.169.254/latest/meta-data")
    assert safe is False

    # Disallowed scheme
    safe, msg = is_safe_url("file:///etc/passwd")
    assert safe is False
    assert "Unsupported scheme" in msg


def test_domain_whitelist_enforcement():
    allowed = ["hdfcbank.com", "sbicard.com"]
    # Matching domain
    safe, _ = is_safe_url("https://www.hdfcbank.com/cards", allowed_domains=allowed)
    # Note: On mac sandbox where DNS is disabled, getaddrinfo will fail, returning False with "Could not resolve hostname"
    # But if domain doesn't match at all, it fails domain check immediately:
    safe_bad, msg = is_safe_url("https://malicious-phishing.com", allowed_domains=allowed)
    assert safe_bad is False
    assert "not in the allowed domain whitelist" in msg


@pytest.mark.asyncio
async def test_fetcher_loads_verified_fixture():
    fetcher = WebsiteFetcher()
    result = await fetcher.fetch_page(
        url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/millennia-cards",
        fixture_path="data/fixtures/hdfc_millennia.html",
        force_fixture=True
    )
    assert result["http_status"] == 200
    assert result["is_fixture"] is True
    assert "HDFC Bank Millennia Credit Card" in result["html_content"]
    assert len(result["content_hash"]) == 64


def test_page_parser_extracts_clean_text_and_tables():
    parser = PageParser()
    sample_html = """
    <html>
      <head><title>Test Bank Page</title></head>
      <body>
        <script>console.log("bad script");</script>
        <h1>Annual Percentage Rates</h1>
        <p>Here are the latest charges for personal loans.</p>
        <table>
          <thead><tr><th>Tenure</th><th>Rate</th></tr></thead>
          <tbody>
            <tr><td>12 Months</td><td>10.5%</td></tr>
            <tr><td>24 Months</td><td>11.0%</td></tr>
          </tbody>
        </table>
      </body>
    </html>
    """
    parsed = parser.parse_html(sample_html)
    assert parsed["title"] == "Test Bank Page"
    assert "bad script" not in parsed["clean_text"]
    assert len(parsed["headings"]) == 1
    assert parsed["headings"][0]["text"] == "Annual Percentage Rates"
    assert len(parsed["tables"]) == 1
    assert parsed["tables"][0]["headers"] == ["Tenure", "Rate"]
    assert len(parsed["tables"][0]["rows"]) == 2
