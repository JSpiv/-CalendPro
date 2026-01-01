"""
ORM models package.

Each model file defines a single SQLAlchemy ORM model class inheriting
from `app.db.base.Base`. All models are imported here so Alembic can
discover them via `target_metadata`.
"""

from app.db.base import Base

# Import model classes so they are registered on Base.metadata
# Identity & accounts
from .user import User  # noqa: F401
from .oauth_account import OAuthAccount  # noqa: F401
from .user_preference import UserPreference  # noqa: F401

# Calendar & external events
from .calendar_source import CalendarSource  # noqa: F401
from .external_event import ExternalEvent  # noqa: F401

# Tasks
from .task_batch import TaskBatch  # noqa: F401
from .task_item import TaskItem  # noqa: F401
from .task_tag import TaskTag  # noqa: F401
from .task_item_tag import TaskItemTag  # noqa: F401

# Plans & exports
from .plan import Plan  # noqa: F401
from .plan_block import PlanBlock  # noqa: F401
from .plan_export import PlanExport  # noqa: F401
from .plan_export_item import PlanExportItem  # noqa: F401

__all__ = [
    "Base",
    # Identity & accounts
    "User",
    "OAuthAccount",
    "UserPreference",
    # Calendar & external events
    "CalendarSource",
    "ExternalEvent",
    # Tasks
    "TaskBatch",
    "TaskItem",
    "TaskTag",
    "TaskItemTag",
    # Plans & exports
    "Plan",
    "PlanBlock",
    "PlanExport",
    "PlanExportItem",
]
