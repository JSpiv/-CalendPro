"""
Event management router.

This module provides endpoints for creating, reading, updating,
and deleting calendar events.
"""

from datetime import datetime
from typing import Optional
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
    EventResponse,
    EventListResponse,
)
from app.services.event_manager import EventManagerService

router = APIRouter(prefix="/events", tags=["events"])
logger = logging.getLogger(__name__)


@router.get("", response_model=EventListResponse)
async def list_events(
    start_min: Optional[datetime] = Query(None, description="Minimum event start time"),
    start_max: Optional[datetime] = Query(None, description="Maximum event start time"),
    calendar_source_id: Optional[str] = Query(None, description="Filter by calendar source"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List events for the current user.

    Can be filtered by time range and calendar source.

    Args:
        start_min: Minimum event start time (inclusive)
        start_max: Maximum event start time (inclusive)
        calendar_source_id: Optional calendar source UUID to filter by
        current_user: The authenticated user
        db: Database session

    Returns:
        List of events
    """
    event_manager = EventManagerService(db)

    try:
        calendar_uuid = UUID(calendar_source_id) if calendar_source_id else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calendar_source_id format"
        )

    events = event_manager.get_events(
        user_id=current_user.id,
        start_min=start_min,
        start_max=start_max,
        calendar_source_id=calendar_uuid,
    )

    return EventListResponse(
        events=events,
        total=len(events)
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific event by ID.

    Args:
        event_id: The event UUID
        current_user: The authenticated user
        db: Database session

    Returns:
        Event details
    """
    # TODO: Add ownership verification
    from sqlalchemy import select
    from app.models.external_event import ExternalEvent

    try:
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event_id format"
        )

    stmt = select(ExternalEvent).where(ExternalEvent.id == event_uuid)
    event = db.execute(stmt).scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # TODO: Verify user owns this event through calendar_source

    return event


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    request: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new event in Google Calendar.

    The event will be created in both Google Calendar and the local database.

    Args:
        request: Event creation data
        current_user: The authenticated user
        db: Database session

    Returns:
        The created event
    """
    event_manager = EventManagerService(db)

    try:
        calendar_uuid = UUID(request.calendar_source_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calendar_source_id format"
        )

    # TODO: Verify user owns this calendar source

    try:
        event = event_manager.create_event(
            calendar_source_id=calendar_uuid,
            title=request.title,
            start_at=request.start_at,
            end_at=request.end_at,
            description=request.description,
            location=request.location,
            all_day=request.all_day,
        )

        logger.info(f"Created event {event.id} for user {current_user.id}")
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    request: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing event.

    Updates will be synced to Google Calendar.

    Args:
        event_id: The event UUID
        request: Event update data
        current_user: The authenticated user
        db: Database session

    Returns:
        The updated event
    """
    event_manager = EventManagerService(db)

    try:
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event_id format"
        )

    # TODO: Verify user owns this event

    try:
        event = event_manager.update_event(
            event_id=event_uuid,
            title=request.title,
            start_at=request.start_at,
            end_at=request.end_at,
            description=request.description,
            location=request.location,
            all_day=request.all_day,
        )

        logger.info(f"Updated event {event_id} for user {current_user.id}")
        return event

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event"
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an event.

    The event will be deleted from both Google Calendar and the local database.

    Args:
        event_id: The event UUID
        current_user: The authenticated user
        db: Database session

    Returns:
        No content (204)
    """
    event_manager = EventManagerService(db)

    try:
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event_id format"
        )

    # TODO: Verify user owns this event

    try:
        event_manager.delete_event(event_id=event_uuid)
        logger.info(f"Deleted event {event_id} for user {current_user.id}")
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )
