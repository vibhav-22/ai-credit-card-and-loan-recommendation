"""
Application logging configuration.
"""
import logging
import sys
from backend.app.core.config import settings

def setup_logging():
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    format_str = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Quiet overly noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("finmatch")
