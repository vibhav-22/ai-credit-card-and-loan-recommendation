"""
Safe website fetcher with SSRF prevention, domain whitelisting,
timeout enforcement, content hashing, and offline fixture fallbacks.
"""
import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import is_safe_url
from backend.app.services.source_discovery import get_allowed_domains, OFFICIAL_SOURCES


class WebsiteFetcher:
    def __init__(self):
        self.user_agent = settings.INGESTION_USER_AGENT
        self.timeout = float(settings.REQUEST_TIMEOUT_SECONDS)
        self.allowed_domains = get_allowed_domains()

    async def fetch_page(
        self,
        url: str,
        fixture_path: Optional[str] = None,
        force_fixture: bool = False
    ) -> Dict[str, Any]:
        """
        Fetches webpage content either from live official URL or verified fixture.
        Returns metadata: url, html_content, content_hash, http_status, fetched_at, is_fixture.
        """
        now = datetime.now(timezone.utc).isoformat()

        # If fixture is forced or network is offline, load fixture directly
        if force_fixture and fixture_path and os.path.exists(fixture_path):
            return self._load_fixture(url, fixture_path, now)

        # 1. SSRF and Domain Security Checks
        safe, reason = is_safe_url(url, allowed_domains=self.allowed_domains)
        if not safe:
            logger.warning(f"URL security check failed for {url}: {reason}")
            # If safe check failed due to local sandbox DNS or domain restriction, use fixture fallback if available
            if fixture_path and os.path.exists(fixture_path):
                logger.info(f"Using verified fixture fallback for {url}")
                return self._load_fixture(url, fixture_path, now)
            raise ValueError(f"Security validation failed for URL: {reason}")

        # 2. Live HTTP fetch with bounded timeout and headers
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=settings.MAX_REDIRECTS
            ) as client:
                resp = await client.get(url, headers=headers)
                
                # Check page size limit (2MB)
                if len(resp.content) > settings.PAGE_SIZE_LIMIT_BYTES:
                    raise ValueError(f"Page size {len(resp.content)} exceeds limit {settings.PAGE_SIZE_LIMIT_BYTES}")

                content_hash = hashlib.sha256(resp.content).hexdigest()
                return {
                    "url": str(resp.url),
                    "original_url": url,
                    "html_content": resp.text,
                    "content_hash": content_hash,
                    "http_status": resp.status_code,
                    "fetched_at": now,
                    "is_fixture": False
                }
        except Exception as e:
            logger.warning(f"Live fetch for {url} failed ({str(e)}). Falling back to fixture.")
            if fixture_path and os.path.exists(fixture_path):
                return self._load_fixture(url, fixture_path, now)
            raise RuntimeError(f"Could not fetch {url} and no valid fixture available: {str(e)}")

    def _load_fixture(self, url: str, fixture_path: str, fetched_at: str) -> Dict[str, Any]:
        with open(fixture_path, "r", encoding="utf-8") as f:
            html = f.read()
        content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        return {
            "url": url,
            "original_url": url,
            "html_content": html,
            "content_hash": content_hash,
            "http_status": 200,
            "fetched_at": fetched_at,
            "is_fixture": True
        }
