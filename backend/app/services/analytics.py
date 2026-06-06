"""Analytics engine: deltas, moving averages, trend detection, velocity."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np

from app.core.logging import get_logger
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.analytics import (
    AnalyticsResponse,
    ComponentAnalytics,
    TrendPoint,
    TrendResponse,
)

logger = get_logger(__name__)

_COMPONENT_FIELDS = {
    "total": "total_score",
    "professional_brand": "professional_brand_score",
    "find_right_people": "find_right_people_score",
    "engage_with_insights": "engage_with_insights_score",
    "build_relationships": "build_relationships_score",
}

_COMPONENT_LABELS = {
    "professional_brand": "Professional Brand",
    "find_right_people": "Find the Right People",
    "engage_with_insights": "Engage with Insights",
    "build_relationships": "Build Relationships",
}


def _scores(snapshots: list[SSISnapshot], field: str) -> list[float]:
    return [getattr(s, field) for s in snapshots]


def _moving_average(values: list[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    return float(np.mean(values[-window:]))


def _trend_direction(values: list[float], lookback: int = 7) -> str:
    """Linear regression slope over last `lookback` points."""
    if len(values) < 2:
        return "stable"
    subset = values[-lookback:]
    if len(subset) < 2:
        return "stable"
    x = np.arange(len(subset), dtype=float)
    slope = float(np.polyfit(x, subset, 1)[0])
    if slope > 0.1:
        return "up"
    elif slope < -0.1:
        return "down"
    return "stable"


def _velocity(values: list[float]) -> Optional[float]:
    """Points gained/lost per week based on linear regression."""
    if len(values) < 3:
        return None
    x = np.arange(len(values), dtype=float)
    slope_per_day = float(np.polyfit(x, values, 1)[0])
    return round(slope_per_day * 7, 2)


def _delta(latest: float, historical: Optional[float]) -> Optional[float]:
    if historical is None:
        return None
    return round(latest - historical, 2)


def _find_snapshot_n_days_ago(
    sorted_snapshots: list[SSISnapshot], n: int
) -> Optional[SSISnapshot]:
    """Return the snapshot closest to `n` days ago from the latest."""
    if not sorted_snapshots:
        return None
    latest_date = sorted_snapshots[-1].snapshot_date
    target = latest_date - timedelta(days=n)
    best = None
    for s in sorted_snapshots:
        if s.snapshot_date <= target:
            best = s
        else:
            break
    return best


def _build_component(
    name: str,
    sorted_snapshots: list[SSISnapshot],
    field: str,
) -> ComponentAnalytics:
    values = _scores(sorted_snapshots, field)
    if not values:
        return ComponentAnalytics(current=0.0)

    current = values[-1]
    snap_1d = _find_snapshot_n_days_ago(sorted_snapshots, 1)
    snap_7d = _find_snapshot_n_days_ago(sorted_snapshots, 7)
    snap_30d = _find_snapshot_n_days_ago(sorted_snapshots, 30)

    return ComponentAnalytics(
        current=round(current, 2),
        delta_1d=_delta(current, getattr(snap_1d, field, None) if snap_1d else None),
        delta_7d=_delta(current, getattr(snap_7d, field, None) if snap_7d else None),
        delta_30d=_delta(current, getattr(snap_30d, field, None) if snap_30d else None),
        avg_7d=_moving_average(values, 7),
        avg_30d=_moving_average(values, 30),
        trend=_trend_direction(values),
        velocity=_velocity(values),
    )


def _generate_insights(
    components: dict[str, ComponentAnalytics],
    snapshots: list[SSISnapshot],
) -> list[str]:
    insights: list[str] = []

    # Weakest component insight
    comp_names = ["professional_brand", "find_right_people", "engage_with_insights", "build_relationships"]
    comp_scores = {k: components[k].current for k in comp_names}
    weakest = min(comp_scores, key=comp_scores.get)
    strongest = max(comp_scores, key=comp_scores.get)

    insights.append(
        f"{_COMPONENT_LABELS[weakest]} is your lowest-scoring component at "
        f"{comp_scores[weakest]:.1f}/25 — focus here for fastest overall improvement."
    )

    # Trend insight
    total = components["total"]
    if total.trend == "up" and total.velocity:
        insights.append(
            f"Your SSI is trending upward at +{total.velocity:.1f} pts/week."
        )
    elif total.trend == "down" and total.velocity:
        insights.append(
            f"Your SSI is trending downward at {total.velocity:.1f} pts/week — action recommended."
        )
    else:
        insights.append("Your SSI score has been relatively stable recently.")

    # 7-day delta insight
    if total.delta_7d is not None:
        sign = "+" if total.delta_7d >= 0 else ""
        insights.append(f"Total SSI changed {sign}{total.delta_7d:.1f} points over the past 7 days.")

    # Best mover
    if len(snapshots) >= 7:
        movers = {
            k: components[k].delta_7d
            for k in comp_names
            if components[k].delta_7d is not None
        }
        if movers:
            best_mover = max(movers, key=lambda k: movers[k])
            if movers[best_mover] > 0:
                insights.append(
                    f"{_COMPONENT_LABELS[best_mover]} showed the best improvement "
                    f"(+{movers[best_mover]:.1f}) this week."
                )

    return insights


def calculate_analytics(sorted_snapshots: list[SSISnapshot]) -> AnalyticsResponse:
    """
    Calculate full analytics from a list of snapshots sorted oldest→newest.
    Requires at least 1 snapshot; richer outputs with 7+ or 30+.
    """
    if not sorted_snapshots:
        raise ValueError("No snapshots provided")

    latest = sorted_snapshots[-1]

    components = {
        name: _build_component(name, sorted_snapshots, field)
        for name, field in _COMPONENT_FIELDS.items()
    }

    comp_names = ["professional_brand", "find_right_people", "engage_with_insights", "build_relationships"]
    comp_scores = {k: components[k].current for k in comp_names}

    insights = _generate_insights(components, sorted_snapshots)

    return AnalyticsResponse(
        as_of_date=latest.snapshot_date,
        total=components["total"],
        professional_brand=components["professional_brand"],
        find_right_people=components["find_right_people"],
        engage_with_insights=components["engage_with_insights"],
        build_relationships=components["build_relationships"],
        industry_avg=latest.industry_avg_score,
        network_avg=latest.network_avg_score,
        data_points=len(sorted_snapshots),
        weakest_component=min(comp_scores, key=comp_scores.get),
        strongest_component=max(comp_scores, key=comp_scores.get),
        insights=insights,
    )


def build_trend_response(
    sorted_snapshots: list[SSISnapshot], period_days: int = 30
) -> TrendResponse:
    cutoff = date.today() - timedelta(days=period_days)
    points = [
        TrendPoint(
            date=s.snapshot_date,
            total_score=s.total_score,
            professional_brand_score=s.professional_brand_score,
            find_right_people_score=s.find_right_people_score,
            engage_with_insights_score=s.engage_with_insights_score,
            build_relationships_score=s.build_relationships_score,
        )
        for s in sorted_snapshots
        if s.snapshot_date >= cutoff
    ]
    return TrendResponse(points=points, period_days=period_days)


def compute_snapshot_deltas(
    snapshot: SSISnapshot,
    sorted_history: list[SSISnapshot],
) -> dict[str, Optional[float]]:
    """Compute 1d / 7d / 30d deltas for a new snapshot given history."""
    s1 = _find_snapshot_n_days_ago(sorted_history, 1)
    s7 = _find_snapshot_n_days_ago(sorted_history, 7)
    s30 = _find_snapshot_n_days_ago(sorted_history, 30)
    return {
        "delta_1d": _delta(snapshot.total_score, s1.total_score if s1 else None),
        "delta_7d": _delta(snapshot.total_score, s7.total_score if s7 else None),
        "delta_30d": _delta(snapshot.total_score, s30.total_score if s30 else None),
    }
