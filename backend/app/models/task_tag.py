"""
TaskTag ORM model.

Represents a category/label for tasks (e.g. "study", "gym", "food").
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class TaskTag(UUIDMixin, TimestampMixin, Base):
    """Task category/label."""

    __tablename__ = "task_tags"

    label: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # hex color code

    # Relationships
    task_items: Mapped[List["TaskItem"]] = relationship(
        "TaskItem",
        secondary="task_item_tags",
        back_populates="tags",
    )
