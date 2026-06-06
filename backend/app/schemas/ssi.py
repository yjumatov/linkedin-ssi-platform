from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SSISnapshotBase(BaseModel):
    snapshot_date: date
    total_score: float = Field(..., ge=0, le=100)
    professional_brand_score: float = Field(..., ge=0, le=25)
    find_right_people_score: float = Field(..., ge=0, le=25)
    engage_with_insights_score: float = Field(..., ge=0, le=25)
    build_relationships_score: float = Field(..., ge=0, le=25)
    industry_avg_score: Optional[float] = None
    network_avg_score: Optional[float] = None


class SSISnapshotCreate(SSISnapshotBase):
    user_id: uuid.UUID
    scraping_run_id: Optional[uuid.UUID] = None
    screenshot_path: Optional[str] = None
    raw_html_path: Optional[str] = None


class SSISnapshotRead(SSISnapshotBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    scraping_run_id: Optional[uuid.UUID] = None
    screenshot_path: Optional[str] = None
    delta_1d: Optional[float] = None
    delta_7d: Optional[float] = None
    delta_30d: Optional[float] = None
    created_at: datetime


class SSILatestResponse(BaseModel):
    snapshot: SSISnapshotRead
    previous: Optional[SSISnapshotRead] = None


class SSIHistoryResponse(BaseModel):
    snapshots: list[SSISnapshotRead]
    total: int
    page: int
    page_size: int
