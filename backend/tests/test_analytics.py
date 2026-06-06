"""Unit tests for analytics engine."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.db.models.ssi_snapshot import SSISnapshot
from app.services.analytics import (
    build_trend_response,
    calculate_analytics,
    compute_snapshot_deltas,
)

_UID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_snapshot(day_offset: int, total: float, **kwargs) -> SSISnapshot:
    snap = SSISnapshot()
    snap.id = uuid.uuid4()
    snap.user_id = _UID
    snap.snapshot_date = date.today() - timedelta(days=day_offset)
    snap.total_score = total
    snap.professional_brand_score = kwargs.get("brand", 13.0)
    snap.find_right_people_score = kwargs.get("people", 14.0)
    snap.engage_with_insights_score = kwargs.get("insights", 13.0)
    snap.build_relationships_score = kwargs.get("rel", 15.0)
    snap.industry_avg_score = None
    snap.network_avg_score = None
    return snap


class TestCalculateAnalytics:
    def test_single_snapshot(self):
        snap = _make_snapshot(0, 60.0, brand=15, people=15, insights=15, rel=15)
        result = calculate_analytics([snap])
        assert result.total.current == 60.0
        assert result.total.delta_1d is None
        assert result.total.delta_7d is None
        assert result.data_points == 1

    def test_deltas_calculated(self):
        snaps = [
            _make_snapshot(7, 50.0, brand=12, people=13, insights=12, rel=13),
            _make_snapshot(0, 60.0, brand=15, people=15, insights=15, rel=15),
        ]
        result = calculate_analytics(snaps)
        assert result.total.current == 60.0
        assert result.total.delta_7d == pytest.approx(10.0, abs=0.1)

    def test_trend_up(self):
        snaps = [_make_snapshot(10 - i, 50.0 + i * 2) for i in range(11)]
        result = calculate_analytics(snaps)
        assert result.total.trend == "up"

    def test_trend_down(self):
        snaps = [_make_snapshot(10 - i, 70.0 - i * 2) for i in range(11)]
        result = calculate_analytics(snaps)
        assert result.total.trend == "down"

    def test_weakest_component_identified(self):
        snap = _make_snapshot(0, 45.0, brand=8, people=14, insights=13, rel=10)
        result = calculate_analytics([snap])
        assert result.weakest_component == "professional_brand"

    def test_insights_generated(self):
        snaps = [_make_snapshot(30 - i, 50.0 + i * 0.5) for i in range(31)]
        result = calculate_analytics(snaps)
        assert len(result.insights) > 0

    def test_velocity_computed_with_enough_data(self):
        snaps = [_make_snapshot(10 - i, 50.0 + i) for i in range(11)]
        result = calculate_analytics(snaps)
        assert result.total.velocity is not None


class TestComputeDeltas:
    def test_delta_computed(self):
        history = [_make_snapshot(7, 55.0)]
        new_snap = _make_snapshot(0, 60.0)
        deltas = compute_snapshot_deltas(new_snap, history)
        assert deltas["delta_7d"] == pytest.approx(5.0)

    def test_no_history(self):
        new_snap = _make_snapshot(0, 60.0)
        deltas = compute_snapshot_deltas(new_snap, [])
        assert deltas["delta_1d"] is None
        assert deltas["delta_7d"] is None
        assert deltas["delta_30d"] is None


class TestTrendResponse:
    def test_filters_by_period(self):
        snaps = [_make_snapshot(60 - i, 50.0 + i * 0.2) for i in range(61)]
        result = build_trend_response(snaps, period_days=30)
        assert all(
            (date.today() - p.date).days <= 30 for p in result.points
        )
        assert result.period_days == 30
