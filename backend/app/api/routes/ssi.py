from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.ssi import SSILatestResponse, SSISnapshotRead, SSIHistoryResponse

router = APIRouter(prefix="/ssi", tags=["ssi"])

_DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def _default_user() -> uuid.UUID:
    return uuid.UUID(_DEFAULT_USER_ID)


@router.get("/latest", response_model=SSILatestResponse)
async def get_latest_ssi(
    user_id: uuid.UUID = Depends(_default_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent SSI snapshot."""
    stmt = (
        select(SSISnapshot)
        .where(SSISnapshot.user_id == user_id)
        .order_by(SSISnapshot.snapshot_date.desc(), SSISnapshot.created_at.desc())
        .limit(2)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No SSI data found — run a scrape first")

    latest = rows[0]
    previous = rows[1] if len(rows) > 1 else None
    return SSILatestResponse(
        snapshot=SSISnapshotRead.model_validate(latest),
        previous=SSISnapshotRead.model_validate(previous) if previous else None,
    )


@router.get("/history", response_model=SSIHistoryResponse)
async def get_ssi_history(
    user_id: uuid.UUID = Depends(_default_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated SSI snapshot history, newest first."""
    offset = (page - 1) * page_size

    count_stmt = select(func.count()).where(SSISnapshot.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(SSISnapshot)
        .where(SSISnapshot.user_id == user_id)
        .order_by(SSISnapshot.snapshot_date.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return SSIHistoryResponse(
        snapshots=[SSISnapshotRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
