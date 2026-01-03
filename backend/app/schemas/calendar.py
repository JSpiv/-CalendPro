"""
Pydantic schemas for calendar-related API endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CalendarSourceResponse(BaseModel):
    """Response schema for a calendar source."""

    id: str
    external_calendar_id: str
    name: str
    is_primary: bool
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OAuthAccountResponse(BaseModel):
    """Response schema for an OAuth account."""

    id: str
    provider: str
    provider_account_id: str
    token_expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarSyncRequest(BaseModel):
    """Request to sync a specific calendar or all calendars."""

    calendar_source_id: Optional[str] = None
    force_full_sync: bool = False


class CalendarSyncResponse(BaseModel):
    """Response from a calendar sync operation."""

    synced_calendars: int
    synced_events: int
    sync_started_at: datetime
    sync_completed_at: datetime
