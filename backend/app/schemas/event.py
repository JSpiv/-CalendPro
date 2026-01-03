"""
Pydantic schemas for event-related API endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class EventBase(BaseModel):
    """Base schema for event data."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    start_at: datetime
    end_at: datetime
    all_day: bool = False


class EventCreateRequest(EventBase):
    """Request to create a new event in Google Calendar."""

    calendar_source_id: str


class EventUpdateRequest(BaseModel):
    """Request to update an existing event."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    all_day: Optional[bool] = None


class EventResponse(BaseModel):
    """Response schema for an event."""

    id: UUID
    calendar_source_id: UUID
    external_event_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: datetime
    end_at: datetime
    all_day: bool
    source: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Response schema for listing events."""

    events: list[EventResponse]
    total: int
