from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Stored encrypted via Fernet
    linkedin_username_enc: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    linkedin_password_enc: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_provider: Mapped[str] = mapped_column(String(32), default="openai", nullable=False)
    notify_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    snapshots: Mapped[list["SSISnapshot"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
    scraping_runs: Mapped[list["ScrapingRun"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
    reports: Mapped[list["ReportHistory"]] = relationship(  # noqa: F821
        back_populates="user", lazy="select"
    )
