"""Shared pytest fixtures."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import User, SSISnapshot
from app.main import app
from app.api.deps import get_db

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"
_DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    # Seed default user
    user = User(
        id=_DEFAULT_USER_ID,
        email="test@example.com",
        linkedin_username_enc="testuser",
        linkedin_password_enc="testpass",
    )
    db_session.add(user)
    await db_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_snapshots(db_session: AsyncSession) -> list[SSISnapshot]:
    """Create 35 days of sample SSI data."""
    snapshots = []
    base_date = date.today() - timedelta(days=34)
    for i in range(35):
        snap = SSISnapshot(
            user_id=_DEFAULT_USER_ID,
            snapshot_date=base_date + timedelta(days=i),
            total_score=55.0 + i * 0.3,
            professional_brand_score=13.0 + i * 0.1,
            find_right_people_score=14.0 + i * 0.05,
            engage_with_insights_score=13.5 + i * 0.08,
            build_relationships_score=14.5 + i * 0.07,
        )
        db_session.add(snap)
        snapshots.append(snap)
    await db_session.commit()
    for s in snapshots:
        await db_session.refresh(s)
    return snapshots
