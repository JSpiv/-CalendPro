"""
Plan ORM model.

Represents one candidate schedule layout produced for a TaskBatch.
"""

from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class Plan(UUIDMixin, TimestampMixin, Base):
    """One candidate schedule for a user's task batch."""

    __tablename__ = "plans"
    __table_args__ = (
        Index(
            "ix_plan_user_created",
            "user_id",
            "created_at",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    calendar_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. draft/selected/rejected

    # Relationships
    user: Mapped["User"] = relationship(back_populates="plans")
    batch: Mapped["TaskBatch"] = relationship(back_populates="plans")
    calendar_source: Mapped[Optional["CalendarSource"]] = relationship()
    blocks: Mapped[List["PlanBlock"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    exports: Mapped[List["PlanExport"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
    )
