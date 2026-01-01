"""
ExternalEvent ORM model.

Cached external calendar events for faster UI and conflict detection.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class ExternalEvent(UUIDMixin, TimestampMixin, Base):
    """Cached external calendar event."""

    __tablename__ = "external_events"
    __table_args__ = (
        Index(
            "ix_external_event_calendar_start",
            "calendar_source_id",
            "start_at",
        ),
        CheckConstraint(
            "(all_day OR end_at > start_at)",
            name="ck_external_event_end_after_start",
        ),
    )

    calendar_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    source: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. imported/generated/manual
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. draft/confirmed/cancelled

    # Relationships
    calendar_source: Mapped["CalendarSource"] = relationship(back_populates="external_events")
