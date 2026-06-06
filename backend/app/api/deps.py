"""FastAPI dependency injection helpers."""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Re-export for convenience in route imports
__all__ = ["get_db"]
