from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.scraping_run import ScrapingRun
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.recommendation import ScrapeRunRead, ScrapeRunResponse
from app.services.analytics import compute_snapshot_deltas
from app.services.linkedin_scraper import LinkedInSSIScraper

router = APIRouter(prefix="/scrape", tags=["scrape"])
logger = get_logger(__name__)

_DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def _default_user() -> uuid.UUID:
    return uuid.UUID(_DEFAULT_USER_ID)


async def _run_scrape(run_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Background task: scrape SSI, persist snapshot, compute deltas."""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        run = await db.get(ScrapingRun, run_id)
        if not run:
            return

        try:
            scraper = LinkedInSSIScraper(
                username=settings.LINKEDIN_USERNAME,
                password=settings.LINKEDIN_PASSWORD,
            )
            data = await scraper.scrape(run_id=str(run_id))

            # Check for duplicate (same date already recorded)
            existing_stmt = (
                select(SSISnapshot)
                .where(
                    SSISnapshot.user_id == user_id,
                    SSISnapshot.snapshot_date == data.scraped_at.date(),
                )
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                # Update in place
                existing.total_score = data.total_score
                existing.professional_brand_score = data.professional_brand_score
                existing.find_right_people_score = data.find_right_people_score
                existing.engage_with_insights_score = data.engage_with_insights_score
                existing.build_relationships_score = data.build_relationships_score
                existing.screenshot_path = data.screenshot_path
                existing.raw_html_path = data.raw_html_path
                existing.scraping_run_id = run_id
                snapshot = existing
            else:
                snapshot = SSISnapshot(
                    user_id=user_id,
                    scraping_run_id=run_id,
                    snapshot_date=data.scraped_at.date(),
                    total_score=data.total_score,
                    professional_brand_score=data.professional_brand_score,
                    find_right_people_score=data.find_right_people_score,
                    engage_with_insights_score=data.engage_with_insights_score,
                    build_relationships_score=data.build_relationships_score,
                    industry_avg_score=data.industry_avg_score,
                    network_avg_score=data.network_avg_score,
                    screenshot_path=data.screenshot_path,
                    raw_html_path=data.raw_html_path,
                )
                db.add(snapshot)
                await db.flush()

            # Compute deltas vs previous snapshots
            history_stmt = (
                select(SSISnapshot)
                .where(SSISnapshot.user_id == user_id, SSISnapshot.id != snapshot.id)
                .order_by(SSISnapshot.snapshot_date.asc())
            )
            history = list((await db.execute(history_stmt)).scalars().all())
            deltas = compute_snapshot_deltas(snapshot, history)
            snapshot.delta_1d = deltas["delta_1d"]
            snapshot.delta_7d = deltas["delta_7d"]
            snapshot.delta_30d = deltas["delta_30d"]

            run.status = "success"
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                "scrape_run_complete",
                run_id=str(run_id),
                total_score=data.total_score,
            )
        except Exception as exc:
            logger.error("scrape_run_failed", run_id=str(run_id), error=str(exc))
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()


@router.post("/run", response_model=ScrapeRunResponse, status_code=202)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger an SSI scrape (runs in background, returns immediately)."""
    run = ScrapingRun(
        user_id=user_id,
        status="running",
        started_at=datetime.now(timezone.utc),
        trigger="manual",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background_tasks.add_task(_run_scrape, run.id, user_id)

    return ScrapeRunResponse(
        run=ScrapeRunRead.model_validate(run),
        message="Scrape started — check /scrape/status for progress",
    )


@router.get("/runs", response_model=list[ScrapeRunRead])
async def list_runs(
    user_id: uuid.UUID = Depends(_default_user),
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List recent scraping runs."""
    stmt = (
        select(ScrapingRun)
        .where(ScrapingRun.user_id == user_id)
        .order_by(ScrapingRun.started_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [ScrapeRunRead.model_validate(r) for r in rows]


@router.get("/runs/{run_id}", response_model=ScrapeRunRead)
async def get_run_status(
    run_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll status of a specific scraping run."""
    run = await db.get(ScrapingRun, run_id)
    if not run or run.user_id != user_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return ScrapeRunRead.model_validate(run)
