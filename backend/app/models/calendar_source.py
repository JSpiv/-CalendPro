"""
CalendarSource ORM model.

Represents a specific calendar (e.g. \"Work\", \"Personal\") within an
external OAuth account.
"""

from __future__ import annotations

from typing import List
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class CalendarSource(UUIDMixin, TimestampMixin, Base):
    """One concrete calendar under an external account."""

    __tablename__ = "calendar_sources"
    __table_args__ = (
        UniqueConstraint(
            "oauth_account_id",
            "external_calendar_id",
            name="uq_calendar_source_account_external_id",
        ),
    )

    oauth_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("oauth_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationships
    oauth_account: Mapped["OAuthAccount"] = relationship(back_populates="calendar_sources")
    external_events: Mapped[List["ExternalEvent"]] = relationship(
        back_populates="calendar_source",
        cascade="all, delete-orphan",
    )
