"""
Security utilities: SSRF checks, domain whitelist validation, API key auth, and session security.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from backend.app.core.config import settings

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

def verify_admin_api_key(api_key: str = Security(api_key_header)) -> bool:
    if not api_key or api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key."
        )
    return True


def is_safe_url(url: str, allowed_domains: list[str] | None = None) -> tuple[bool, str]:
    """
    Validates a URL against SSRF attacks:
    - Must be http or https
    - Hostname must resolve to a public, non-private IP
    - If allowed_domains is provided, hostname must match an allowed domain
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL."
        
        # Check against allowed domains if specified
        if allowed_domains:
            domain_match = any(
                hostname == d or hostname.endswith("." + d)
                for d in allowed_domains
            )
            if not domain_match:
                return False, f"Domain '{hostname}' is not in the allowed domain whitelist."
        
        # Resolve hostname to IP to block localhost, private IPs, link-local, cloud metadata
        # (e.g. 169.254.169.254, 127.0.0.1, 10.x, 192.168.x)
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                    return False, f"Host '{hostname}' resolves to restricted IP: {ip_str}."
        except socket.gaierror:
            # If domain cannot be resolved at validation time, flag as error
            return False, f"Could not resolve hostname '{hostname}'."
            
        return True, "URL is safe."
    except Exception as e:
        return False, f"Error validating URL: {str(e)}"
