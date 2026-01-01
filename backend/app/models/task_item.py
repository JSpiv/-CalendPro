"""
TaskItem ORM model.

Represents a single parsed line from a TaskBatch.
"""

from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class TaskItem(UUIDMixin, TimestampMixin, Base):
    """One parsed task line from a batch."""

    __tablename__ = "task_items"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_batches.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    parsed_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parse_method: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. regex_v1, ml_v1

    # Relationships
    batch: Mapped["TaskBatch"] = relationship(back_populates="task_items")
    tags: Mapped[List["TaskTag"]] = relationship(
        "TaskTag",
        secondary="task_item_tags",
        back_populates="task_items",
    )
    plan_blocks: Mapped[List["PlanBlock"]] = relationship(
        back_populates="task_item",
    )
