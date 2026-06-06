from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class ComponentAnalytics(BaseModel):
    current: float
    delta_1d: Optional[float] = None
    delta_7d: Optional[float] = None
    delta_30d: Optional[float] = None
    avg_7d: Optional[float] = None
    avg_30d: Optional[float] = None
    trend: str = "stable"  # up | down | stable
    velocity: Optional[float] = None  # points per week


class AnalyticsResponse(BaseModel):
    as_of_date: date
    total: ComponentAnalytics
    professional_brand: ComponentAnalytics
    find_right_people: ComponentAnalytics
    engage_with_insights: ComponentAnalytics
    build_relationships: ComponentAnalytics
    industry_avg: Optional[float] = None
    network_avg: Optional[float] = None
    data_points: int
    weakest_component: Optional[str] = None
    strongest_component: Optional[str] = None
    insights: list[str] = []


class TrendPoint(BaseModel):
    date: date
    total_score: float
    professional_brand_score: float
    find_right_people_score: float
    engage_with_insights_score: float
    build_relationships_score: float


class TrendResponse(BaseModel):
    points: list[TrendPoint]
    period_days: int
