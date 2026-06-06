from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    snapshot_id: Optional[uuid.UUID] = None
    category: str
    priority: str
    title: str
    root_cause: str
    recommendation: str
    expected_impact: str
    action_steps: Optional[str] = None
    ai_provider: str
    ai_model: Optional[str] = None
    is_read: bool
    is_dismissed: bool
    created_at: datetime


class RecommendationsResponse(BaseModel):
    recommendations: list[RecommendationRead]
    total: int
    unread: int


class RecommendationUpdateRequest(BaseModel):
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class ScrapeRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    trigger: str


class ScrapeRunResponse(BaseModel):
    run: ScrapeRunRead
    message: str
