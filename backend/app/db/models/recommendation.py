from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Recommendation(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ssi_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Categorisation
    category: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # overall | professional_brand | find_right_people | engage_insights | build_relationships
    priority: Mapped[str] = mapped_column(String(16), nullable=False)  # high | medium | low

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)
    action_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Metadata
    ai_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="openai")
    ai_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="recommendations")  # noqa: F821
    snapshot: Mapped[Optional["SSISnapshot"]] = relationship(  # noqa: F821
        back_populates="recommendations"
    )
