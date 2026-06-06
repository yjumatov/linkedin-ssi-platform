from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class SSISnapshot(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "ssi_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scraping_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scraping_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Core SSI scores
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    professional_brand_score: Mapped[float] = mapped_column(Float, nullable=False)
    find_right_people_score: Mapped[float] = mapped_column(Float, nullable=False)
    engage_with_insights_score: Mapped[float] = mapped_column(Float, nullable=False)
    build_relationships_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Industry / network context (scraped alongside scores)
    industry_avg_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    network_avg_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Storage paths
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    raw_html_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Computed deltas (filled by analytics service after save)
    delta_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delta_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delta_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="snapshots")  # noqa: F821
    scraping_run: Mapped[Optional["ScrapingRun"]] = relationship(  # noqa: F821
        back_populates="snapshot"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        back_populates="snapshot", lazy="select"
    )
