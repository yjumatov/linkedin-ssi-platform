"""APScheduler background job runner for scraping and reporting."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging(debug=settings.DEBUG)
logger = get_logger(__name__)

_DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def run_scheduled_scrape() -> None:
    """Daily scrape job."""
    from app.db.session import AsyncSessionLocal
    from app.db.models.scraping_run import ScrapingRun
    from app.db.models.ssi_snapshot import SSISnapshot
    from sqlalchemy import select
    from app.services.linkedin_scraper import LinkedInSSIScraper
    from app.services.analytics import compute_snapshot_deltas

    logger.info("scheduled_scrape_starting")
    async with AsyncSessionLocal() as db:
        run = ScrapingRun(
            user_id=_DEFAULT_USER_ID,
            status="running",
            started_at=datetime.now(timezone.utc),
            trigger="scheduled",
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        try:
            scraper = LinkedInSSIScraper(
                username=settings.LINKEDIN_USERNAME,
                password=settings.LINKEDIN_PASSWORD,
            )
            data = await scraper.scrape(run_id=str(run.id))

            existing_stmt = select(SSISnapshot).where(
                SSISnapshot.user_id == _DEFAULT_USER_ID,
                SSISnapshot.snapshot_date == data.scraped_at.date(),
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing.total_score = data.total_score
                existing.professional_brand_score = data.professional_brand_score
                existing.find_right_people_score = data.find_right_people_score
                existing.engage_with_insights_score = data.engage_with_insights_score
                existing.build_relationships_score = data.build_relationships_score
                existing.screenshot_path = data.screenshot_path
                existing.raw_html_path = data.raw_html_path
                snapshot = existing
            else:
                snapshot = SSISnapshot(
                    user_id=_DEFAULT_USER_ID,
                    scraping_run_id=run.id,
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

            history_stmt = (
                select(SSISnapshot)
                .where(SSISnapshot.user_id == _DEFAULT_USER_ID, SSISnapshot.id != snapshot.id)
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
            logger.info("scheduled_scrape_success", score=data.total_score)

        except Exception as exc:
            logger.error("scheduled_scrape_failed", error=str(exc))
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()


async def run_daily_report() -> None:
    """Daily email report job."""
    from app.db.session import AsyncSessionLocal
    from app.db.models.ssi_snapshot import SSISnapshot
    from app.db.models.recommendation import Recommendation
    from app.db.models.report_history import ReportHistory
    from sqlalchemy import select
    from app.services.analytics import calculate_analytics
    from app.services.reporting import send_daily_report
    from datetime import date

    if not settings.REPORT_TO_EMAIL:
        logger.info("report_skipped_no_email")
        return

    logger.info("daily_report_starting")
    async with AsyncSessionLocal() as db:
        history_stmt = (
            select(SSISnapshot)
            .where(SSISnapshot.user_id == _DEFAULT_USER_ID)
            .order_by(SSISnapshot.snapshot_date.asc())
        )
        snapshots = list((await db.execute(history_stmt)).scalars().all())
        if not snapshots:
            logger.warning("report_skipped_no_data")
            return

        analytics = calculate_analytics(snapshots)

        recs_stmt = (
            select(Recommendation)
            .where(Recommendation.user_id == _DEFAULT_USER_ID, Recommendation.is_dismissed.is_(False))
            .order_by(Recommendation.created_at.desc())
            .limit(5)
        )
        recs = list((await db.execute(recs_stmt)).scalars().all())
        rec_dicts = [
            {
                "title": r.title,
                "recommendation": r.recommendation,
                "priority": r.priority,
                "category": r.category,
            }
            for r in recs
        ]

        report_date = date.today()
        status = "sent"
        error_msg = None

        try:
            await send_daily_report(analytics, rec_dicts, settings.REPORT_TO_EMAIL, report_date)
        except Exception as exc:
            status = "failed"
            error_msg = str(exc)
            logger.error("report_send_failed", error=str(exc))

        report = ReportHistory(
            user_id=_DEFAULT_USER_ID,
            report_type="daily",
            report_date=report_date,
            email_sent_to=settings.REPORT_TO_EMAIL,
            status=status,
            error_message=error_msg,
        )
        db.add(report)
        await db.commit()


async def main() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        run_scheduled_scrape,
        CronTrigger.from_crontab(settings.SCRAPE_CRON),
        id="daily_scrape",
        name="Daily LinkedIn SSI Scrape",
        max_instances=1,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_daily_report,
        CronTrigger.from_crontab(settings.REPORT_CRON),
        id="daily_report",
        name="Daily Email Report",
        max_instances=1,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        scrape_cron=settings.SCRAPE_CRON,
        report_cron=settings.REPORT_CRON,
    )

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(main())
