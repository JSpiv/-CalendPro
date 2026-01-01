"""
SQLAlchemy ORM base and common exports.

All ORM models should inherit from `Base` and use the SQLAlchemy 2.0
typed ORM helpers re-exported here.
"""

from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


__all__ = [
    "Base",
    "Mapped",
    "mapped_column",
]
