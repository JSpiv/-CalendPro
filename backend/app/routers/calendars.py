"""
Calendar management router.

This module provides endpoints for listing calendars and triggering syncs.
"""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.calendar_source import CalendarSource
from app.models.oauth_account import OAuthAccount
from app.schemas.calendar import (
    CalendarSourceResponse,
    CalendarSyncRequest,
    CalendarSyncResponse,
)
from app.services.calendar_sync import CalendarSyncService

router = APIRouter(prefix="/calendars", tags=["calendars"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[CalendarSourceResponse])
async def list_calendars(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all calendar sources for the current user.

    Returns all calendars from all connected OAuth accounts.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        List of calendar sources
    """
    # Query calendar sources for this user through their OAuth accounts
    stmt = (
        select(CalendarSource)
        .join(OAuthAccount, CalendarSource.oauth_account_id == OAuthAccount.id)
        .where(OAuthAccount.user_id == current_user.id)
        .order_by(CalendarSource.is_primary.desc(), CalendarSource.name)
    )

    calendar_sources = db.execute(stmt).scalars().all()

    return calendar_sources


@router.get("/{calendar_id}", response_model=CalendarSourceResponse)
async def get_calendar(
    calendar_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details for a specific calendar source.

    Args:
        calendar_id: The calendar source UUID
        current_user: The authenticated user
        db: Database session

    Returns:
        Calendar source details
    """
    # Query with ownership check
    stmt = (
        select(CalendarSource)
        .join(OAuthAccount, CalendarSource.oauth_account_id == OAuthAccount.id)
        .where(
            CalendarSource.id == calendar_id,
            OAuthAccount.user_id == current_user.id
        )
    )

    calendar_source = db.execute(stmt).scalar_one_or_none()

    if not calendar_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )

    return calendar_source


@router.post("/sync", response_model=CalendarSyncResponse)
async def sync_calendars(
    request: CalendarSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger a calendar sync operation.

    This will fetch the latest calendars and events from Google Calendar
    and update the local database cache.

    Args:
        request: Sync configuration
        current_user: The authenticated user
        db: Database session

    Returns:
        Sync results
    """
    sync_service = CalendarSyncService(db)
    sync_started_at = datetime.now(timezone.utc)

    try:
        if request.calendar_source_id:
            # Sync specific calendar
            # First verify ownership
            stmt = (
                select(CalendarSource)
                .join(OAuthAccount, CalendarSource.oauth_account_id == OAuthAccount.id)
                .where(
                    CalendarSource.id == request.calendar_source_id,
                    OAuthAccount.user_id == current_user.id
                )
            )
            calendar_source = db.execute(stmt).scalar_one_or_none()

            if not calendar_source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Calendar not found"
                )

            events_synced = sync_service.sync_calendar_source(request.calendar_source_id)
            calendars_synced = 1
        else:
            # Sync all calendars for user
            calendars_synced, events_synced = sync_service.sync_user_calendars(
                str(current_user.id)
            )

        sync_completed_at = datetime.now(timezone.utc)

        logger.info(
            f"Synced {calendars_synced} calendar(s) and {events_synced} event(s) "
            f"for user {current_user.id}"
        )

        return CalendarSyncResponse(
            synced_calendars=calendars_synced,
            synced_events=events_synced,
            sync_started_at=sync_started_at,
            sync_completed_at=sync_completed_at,
        )

    except Exception as e:
        logger.error(f"Calendar sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calendar sync failed: {str(e)}"
        )
