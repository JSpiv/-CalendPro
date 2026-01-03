"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.task import TaskBatchRequest, TaskBatchResponse, ParsedTask
from app.schemas.calendar import (
    CalendarSourceResponse,
    OAuthAccountResponse,
    CalendarSyncRequest,
    CalendarSyncResponse,
)
from app.schemas.event import (
    EventBase,
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventListResponse,
)

__all__ = [
    # Task schemas
    "TaskBatchRequest",
    "TaskBatchResponse",
    "ParsedTask",
    # Calendar schemas
    "CalendarSourceResponse",
    "OAuthAccountResponse",
    "CalendarSyncRequest",
    "CalendarSyncResponse",
    # Event schemas
    "EventBase",
    "EventCreateRequest",
    "EventUpdateRequest",
    "EventResponse",
    "EventListResponse",
]
