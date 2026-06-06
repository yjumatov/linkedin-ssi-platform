from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "LinkedIn SSI Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(default="postgresql+asyncpg://ssi:ssi@localhost:5432/ssi_db")
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default="change-me-in-production-32-chars!!")
    ENCRYPTION_KEY: str = Field(default="change-me-fernet-key-base64-32ch=")

    # ── LinkedIn ──────────────────────────────────────────────────────────────
    LINKEDIN_USERNAME: str = Field(default="")
    LINKEDIN_PASSWORD: str = Field(default="")
    LINKEDIN_SSI_URL: str = "https://www.linkedin.com/sales/ssi"

    # ── AI Provider ───────────────────────────────────────────────────────────
    AI_PROVIDER: str = Field(default="openai")  # "openai" | "claude"
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_USE_TLS: bool = True
    REPORT_FROM_EMAIL: str = Field(default="noreply@example.com")
    REPORT_TO_EMAIL: str = Field(default="")

    # ── Scheduling ────────────────────────────────────────────────────────────
    SCRAPE_CRON: str = "0 9 * * *"   # 09:00 UTC daily
    REPORT_CRON: str = "0 10 * * *"  # 10:00 UTC daily

    # ── Storage ───────────────────────────────────────────────────────────────
    DATA_DIR: str = "/app/data"

    @property
    def screenshots_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "screenshots")

    @property
    def cookies_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "cookies")

    @property
    def html_dir(self) -> str:
        return os.path.join(self.DATA_DIR, "html")

    # ── Scraping ──────────────────────────────────────────────────────────────
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 5
    BROWSER_HEADLESS: bool = True
    PAGE_TIMEOUT_MS: int = 30_000

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
