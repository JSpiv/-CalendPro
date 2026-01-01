"""
TaskItemTag ORM model.

Many-to-many join table between TaskItem and TaskTag.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class TaskItemTag(UUIDMixin, TimestampMixin, Base):
    """Association between a task item and a tag."""

    __tablename__ = "task_item_tags"
    __table_args__ = (
        UniqueConstraint(
            "task_item_id",
            "task_tag_id",
            name="uq_task_item_tag_unique",
        ),
    )

    task_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    task_tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_tags.id", ondelete="CASCADE"),
        nullable=False,
    )
