"""
TaskBatch ORM model.

Represents a single pasted text submission by a user.
"""

from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class TaskBatch(UUIDMixin, TimestampMixin, Base):
    """One paste/upload of multiline text from a user."""

    __tablename__ = "task_batches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. paste/upload
    default_timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="task_batches")
    task_items: Mapped[List["TaskItem"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    plans: Mapped[List["Plan"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )
