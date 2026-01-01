"""
PlanExport ORM model.

Tracks when a Plan is exported/published to an external calendar.
"""

from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class PlanExport(UUIDMixin, TimestampMixin, Base):
    """Record of exporting a plan to an external calendar."""

    __tablename__ = "plan_exports"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    calendar_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. pending/completed/failed
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    # Relationships
    plan: Mapped["Plan"] = relationship(back_populates="exports")
    calendar_source: Mapped["CalendarSource"] = relationship()
    items: Mapped[List["PlanExportItem"]] = relationship(
        back_populates="plan_export",
        cascade="all, delete-orphan",
    )
