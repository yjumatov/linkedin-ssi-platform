"""Integration tests for FastAPI endpoints."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.anyio
class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data


@pytest.mark.anyio
class TestSSIEndpoints:
    async def test_latest_404_when_no_data(self, client: AsyncClient):
        resp = await client.get("/ssi/latest")
        assert resp.status_code == 404

    async def test_history_empty(self, client: AsyncClient):
        resp = await client.get("/ssi/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["snapshots"] == []

    async def test_latest_returns_snapshot(self, client: AsyncClient, sample_snapshots):
        resp = await client.get("/ssi/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "snapshot" in data
        assert data["snapshot"]["total_score"] > 0

    async def test_history_pagination(self, client: AsyncClient, sample_snapshots):
        resp = await client.get("/ssi/history?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["snapshots"]) == 10
        assert data["total"] == 35
        assert data["page"] == 1


@pytest.mark.anyio
class TestAnalyticsEndpoints:
    async def test_analytics_404_no_data(self, client: AsyncClient):
        resp = await client.get("/analytics")
        assert resp.status_code == 404

    async def test_analytics_with_data(self, client: AsyncClient, sample_snapshots):
        resp = await client.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "professional_brand" in data
        assert data["data_points"] == 35

    async def test_trends_endpoint(self, client: AsyncClient, sample_snapshots):
        resp = await client.get("/analytics/trends?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data
        assert len(data["points"]) > 0


@pytest.mark.anyio
class TestRecommendationsEndpoint:
    async def test_list_empty(self, client: AsyncClient):
        resp = await client.get("/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    async def test_patch_not_found(self, client: AsyncClient):
        import uuid
        fake_id = str(uuid.uuid4())
        resp = await client.patch(
            f"/recommendations/{fake_id}",
            json={"is_read": True},
        )
        assert resp.status_code == 404


@pytest.mark.anyio
class TestScrapeEndpoints:
    async def test_list_runs_empty(self, client: AsyncClient):
        resp = await client.get("/scrape/runs")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_run_not_found(self, client: AsyncClient):
        import uuid
        resp = await client.get(f"/scrape/runs/{uuid.uuid4()}")
        assert resp.status_code == 404
