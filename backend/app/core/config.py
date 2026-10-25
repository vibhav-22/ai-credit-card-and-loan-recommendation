"""
Application configuration management using Pydantic Settings.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FinMatch AI - Credit Card & Loan Recommender"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production-only"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    ADMIN_API_KEY: str = "admin-secret-dev-key"

    # Database
    DATABASE_URL: str = "sqlite:///./finmatch.db"

    # LLM Settings
    # Supported: mock, gemini, openai, anthropic
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    MOCK_LLM_LATENCY_SECONDS: float = 0.0

    # Ingestion & Fetching Settings
    INGESTION_USER_AGENT: str = "FinMatchBot/1.0 (+https://finmatch.local/robot)"
    REQUEST_TIMEOUT_SECONDS: int = 15
    MAX_REDIRECTS: int = 5
    PAGE_SIZE_LIMIT_BYTES: int = 2 * 1024 * 1024  # 2MB
    STALE_DATA_DAYS_THRESHOLD: int = 30

    # Disallowed/private IPs for SSRF protection
    BLOCKED_IP_NETWORKS: List[str] = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "::1/128",
        "fc00::/7",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
