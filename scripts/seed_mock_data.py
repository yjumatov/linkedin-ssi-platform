#!/usr/bin/env python3
"""Seed 90 days of realistic mock SSI data for development and demo purposes.

Usage:
    cd backend
    DATABASE_URL=postgresql+asyncpg://ssi:ssi@localhost:5432/ssi_db \
        python ../scripts/seed_mock_data.py
"""
from __future__ import annotations

import asyncio
import math
import random
import sys
import uuid
from datetime import date, timedelta

# Ensure backend app is importable
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import SSISnapshot, User


_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_BASE_DATE = date.today() - timedelta(days=89)


def _generate_score(day: int, base: float, amplitude: float, noise: float = 1.0) -> float:
    """Simulated SSI component score with trend + weekly cycle + noise."""
    trend = day * 0.05
    cycle = amplitude * math.sin(2 * math.pi * day / 7)
    randomness = random.gauss(0, noise)
    return max(0.0, min(base + trend + cycle + randomness, 25.0))


async def seed(db_url: str) -> None:
    engine = create_async_engine(db_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        existing = await db.get(User, _USER_ID)
        if not existing:
            user = User(
                id=_USER_ID,
                email="demo@example.com",
                full_name="Demo User",
                linkedin_username_enc="demo@example.com",
                linkedin_password_enc="demo_password",
            )
            db.add(user)
            await db.flush()

        for i in range(90):
            d = _BASE_DATE + timedelta(days=i)
            brand = _generate_score(i, 14, 0.8, 0.5)
            people = _generate_score(i, 13, 0.6, 0.4)
            insights = _generate_score(i, 12, 1.0, 0.6)
            relationships = _generate_score(i, 15, 0.5, 0.3)
            total = round(brand + people + insights + relationships, 1)

            snap = SSISnapshot(
                user_id=_USER_ID,
                snapshot_date=d,
                total_score=total,
                professional_brand_score=round(brand, 1),
                find_right_people_score=round(people, 1),
                engage_with_insights_score=round(insights, 1),
                build_relationships_score=round(relationships, 1),
                industry_avg_score=round(random.uniform(38, 42), 1),
                network_avg_score=round(random.uniform(42, 48), 1),
            )
            db.add(snap)

        await db.commit()
        print(f"Seeded 90 snapshots for user {_USER_ID}")

    await engine.dispose()


if __name__ == "__main__":
    url = settings.DATABASE_URL
    asyncio.run(seed(url))
