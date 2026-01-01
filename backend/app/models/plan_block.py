"""
PlanBlock ORM model.

Represents a single scheduled block of time within a Plan.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class PlanBlock(UUIDMixin, TimestampMixin, Base):
    """One scheduled time block in a plan."""

    __tablename__ = "plan_blocks"
    __table_args__ = (
        Index(
            "ix_plan_block_plan_start",
            "plan_id",
            "start_at",
        ),
        CheckConstraint(
            "end_at > start_at",
            name="ck_plan_block_end_after_start",
        ),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    task_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("external_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    plan: Mapped["Plan"] = relationship(back_populates="blocks")
    task_item: Mapped["TaskItem"] = relationship(back_populates="plan_blocks")
    external_event: Mapped[Optional["ExternalEvent"]] = relationship()
    export_items: Mapped[List["PlanExportItem"]] = relationship(
        back_populates="plan_block",
        cascade="all, delete-orphan",
    )
