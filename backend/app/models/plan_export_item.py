"""
PlanExportItem ORM model.

Maps individual PlanBlocks to external calendar event IDs after export.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class PlanExportItem(UUIDMixin, TimestampMixin, Base):
    """Mapping of a plan block to an external calendar event."""

    __tablename__ = "plan_export_items"
    __table_args__ = (
        UniqueConstraint(
            "plan_export_id",
            "plan_block_id",
            name="uq_plan_export_item_unique",
        ),
    )

    plan_export_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plan_exports.id", ondelete="CASCADE"),
        nullable=False,
    )

    plan_block_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plan_blocks.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    plan_export: Mapped["PlanExport"] = relationship(back_populates="items")
    plan_block: Mapped["PlanBlock"] = relationship(back_populates="export_items")
