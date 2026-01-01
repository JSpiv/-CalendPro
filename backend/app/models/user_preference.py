"""
UserPreference ORM model.

Stores per-user configuration such as work hours, break rules,
default calendar, and other flexible settings.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class UserPreference(UUIDMixin, TimestampMixin, Base):
    """Per-user preferences and settings."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preference_user"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Optional simple fields for common preferences
    default_timezone: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Flexible JSON blob for additional settings
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="preferences")
