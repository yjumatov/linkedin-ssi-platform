"""FastAPI application entrypoint."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analytics, health, recommendations, scrape, ssi
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(debug=settings.DEBUG)
    logger.info("startup", version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    # Ensure data directories exist
    for d in [settings.screenshots_dir, settings.cookies_dir, settings.html_dir]:
        os.makedirs(d, exist_ok=True)

    # Seed default user row if DB is fresh (dev convenience)
    try:
        await _seed_default_user()
    except Exception as exc:
        logger.warning("seed_user_failed", error=str(exc))

    yield
    logger.info("shutdown")


async def _seed_default_user() -> None:
    """Create a default user row so API works without an auth flow."""
    import uuid
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models.user import User

    default_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    async with AsyncSessionLocal() as db:
        existing = await db.get(User, default_id)
        if not existing:
            user = User(
                id=default_id,
                email=settings.LINKEDIN_USERNAME or "admin@example.com",
                full_name="SSI Admin",
                linkedin_username_enc=settings.LINKEDIN_USERNAME,
                linkedin_password_enc=settings.LINKEDIN_PASSWORD,
                ai_provider=settings.AI_PROVIDER,
                notify_email=settings.REPORT_TO_EMAIL or settings.LINKEDIN_USERNAME,
            )
            db.add(user)
            await db.commit()
            logger.info("default_user_seeded")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Automated LinkedIn Social Selling Index tracking, analytics, "
        "and AI-powered recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(ssi.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(scrape.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now(timezone.utc).isoformat()},
    )
