from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.analytics import AnalyticsResponse, TrendResponse
from app.services.analytics import build_trend_response, calculate_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

_DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def _default_user() -> uuid.UUID:
    return uuid.UUID(_DEFAULT_USER_ID)


async def _load_snapshots(user_id: uuid.UUID, db: AsyncSession) -> list[SSISnapshot]:
    stmt = (
        select(SSISnapshot)
        .where(SSISnapshot.user_id == user_id)
        .order_by(SSISnapshot.snapshot_date.asc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Full analytics: deltas, moving averages, trends, velocity, insights."""
    snapshots = await _load_snapshots(user_id, db)
    if not snapshots:
        raise HTTPException(status_code=404, detail="No SSI data found")
    return calculate_analytics(snapshots)


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    user_id: uuid.UUID = Depends(_default_user),
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Time-series data for trend charts."""
    snapshots = await _load_snapshots(user_id, db)
    if not snapshots:
        raise HTTPException(status_code=404, detail="No SSI data found")
    return build_trend_response(snapshots, period_days=days)
