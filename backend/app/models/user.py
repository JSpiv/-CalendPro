"""
User ORM model.

Core identity for the application. Owns calendars, tasks, plans,
preferences, and external accounts.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """Application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),  # RFC-style max for email
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    task_batches: Mapped[List["TaskBatch"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preferences: Mapped[Optional["UserPreference"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    plans: Mapped[List["Plan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
