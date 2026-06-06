from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.recommendation import Recommendation
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.recommendation import (
    RecommendationRead,
    RecommendationUpdateRequest,
    RecommendationsResponse,
)
from app.services.analytics import calculate_analytics
from app.services.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

_DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def _default_user() -> uuid.UUID:
    return uuid.UUID(_DEFAULT_USER_ID)


@router.get("", response_model=RecommendationsResponse)
async def list_recommendations(
    user_id: uuid.UUID = Depends(_default_user),
    include_dismissed: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List AI recommendations, newest first."""
    stmt = select(Recommendation).where(Recommendation.user_id == user_id)
    if not include_dismissed:
        stmt = stmt.where(Recommendation.is_dismissed.is_(False))
    stmt = stmt.order_by(Recommendation.created_at.desc())

    rows = (await db.execute(stmt)).scalars().all()

    unread_count = sum(1 for r in rows if not r.is_read)
    return RecommendationsResponse(
        recommendations=[RecommendationRead.model_validate(r) for r in rows],
        total=len(rows),
        unread=unread_count,
    )


@router.post("/generate", response_model=RecommendationsResponse)
async def generate(
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI recommendation generation based on current SSI data."""
    snapshots_stmt = (
        select(SSISnapshot)
        .where(SSISnapshot.user_id == user_id)
        .order_by(SSISnapshot.snapshot_date.asc())
    )
    snapshots = list((await db.execute(snapshots_stmt)).scalars().all())
    if not snapshots:
        raise HTTPException(status_code=404, detail="No SSI data found — run a scrape first")

    analytics = calculate_analytics(snapshots)
    latest_snapshot = snapshots[-1]
    rec_dicts = await generate_recommendations(analytics, snapshots)

    new_recs: list[Recommendation] = []
    for rd in rec_dicts:
        rec = Recommendation(
            user_id=user_id,
            snapshot_id=latest_snapshot.id,
            **rd,
        )
        db.add(rec)
        new_recs.append(rec)

    await db.commit()
    for rec in new_recs:
        await db.refresh(rec)

    return RecommendationsResponse(
        recommendations=[RecommendationRead.model_validate(r) for r in new_recs],
        total=len(new_recs),
        unread=len(new_recs),
    )


@router.patch("/{rec_id}", response_model=RecommendationRead)
async def update_recommendation(
    rec_id: uuid.UUID,
    body: RecommendationUpdateRequest,
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark recommendation as read or dismissed."""
    rec = await db.get(Recommendation, rec_id)
    if not rec or rec.user_id != user_id:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    if body.is_read is not None:
        rec.is_read = body.is_read
    if body.is_dismissed is not None:
        rec.is_dismissed = body.is_dismissed

    await db.commit()
    await db.refresh(rec)
    return RecommendationRead.model_validate(rec)
