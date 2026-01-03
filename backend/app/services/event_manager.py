"""
Event management service.

This module handles business logic for creating, updating, and deleting
events in both Google Calendar and the local database.
"""

from datetime import datetime
from typing import Optional
import logging
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.calendar_source import CalendarSource
from app.models.external_event import ExternalEvent
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class EventManagerService:
    """Service for managing calendar events."""

    def __init__(self, db: Session):
        """
        Initialize the event manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_event(
        self,
        calendar_source_id: UUID,
        title: str,
        start_at: datetime,
        end_at: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: bool = False,
    ) -> ExternalEvent:
        """
        Create a new event in Google Calendar and save to local database.

        Args:
            calendar_source_id: The calendar source to create the event in
            title: Event title
            start_at: Event start time
            end_at: Event end time
            description: Event description
            location: Event location
            all_day: Whether this is an all-day event

        Returns:
            The created ExternalEvent
        """
        # Validate times
        if end_at <= start_at:
            raise ValueError("Event end time must be after start time")

        # Get the calendar source
        stmt = select(CalendarSource).where(CalendarSource.id == calendar_source_id)
        calendar_source = self.db.execute(stmt).scalar_one_or_none()

        if not calendar_source:
            raise ValueError(f"Calendar source {calendar_source_id} not found")

        # Create event in Google Calendar
        oauth_account = calendar_source.oauth_account
        google_service = GoogleCalendarService(oauth_account, self.db)

        try:
            google_event = google_service.create_event(
                calendar_id=calendar_source.external_calendar_id,
                title=title,
                start=start_at,
                end=end_at,
                description=description,
                location=location,
                all_day=all_day,
            )

            # Save to local database
            external_event = ExternalEvent(
                calendar_source_id=calendar_source.id,
                external_event_id=google_event["id"],
                title=title,
                description=description,
                location=location,
                start_at=start_at,
                end_at=end_at,
                all_day=all_day,
                source="generated",
                status="confirmed",
            )
            self.db.add(external_event)
            self.db.commit()
            self.db.refresh(external_event)

            logger.info(f"Created event {external_event.id} in calendar {calendar_source.name}")
            return external_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create event: {e}")
            raise

    def update_event(
        self,
        event_id: UUID,
        title: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: Optional[bool] = None,
    ) -> ExternalEvent:
        """
        Update an existing event in Google Calendar and local database.

        Args:
            event_id: The external event UUID
            title: New event title
            start_at: New start time
            end_at: New end time
            description: New description
            location: New location
            all_day: Whether this is an all-day event

        Returns:
            The updated ExternalEvent
        """
        # Get the event
        stmt = select(ExternalEvent).where(ExternalEvent.id == event_id)
        external_event = self.db.execute(stmt).scalar_one_or_none()

        if not external_event:
            raise ValueError(f"Event {event_id} not found")

        if not external_event.external_event_id:
            raise ValueError(f"Event {event_id} does not have a Google Calendar ID")

        # Validate times if both provided
        if start_at and end_at and end_at <= start_at:
            raise ValueError("Event end time must be after start time")

        # Get the calendar source and OAuth account
        calendar_source = external_event.calendar_source
        oauth_account = calendar_source.oauth_account
        google_service = GoogleCalendarService(oauth_account, self.db)

        try:
            # Update in Google Calendar
            google_event = google_service.update_event(
                calendar_id=calendar_source.external_calendar_id,
                event_id=external_event.external_event_id,
                title=title,
                start=start_at,
                end=end_at,
                description=description,
                location=location,
                all_day=all_day,
            )

            # Update local database
            if title is not None:
                external_event.title = title
            if description is not None:
                external_event.description = description
            if location is not None:
                external_event.location = location
            if start_at is not None:
                external_event.start_at = start_at
            if end_at is not None:
                external_event.end_at = end_at
            if all_day is not None:
                external_event.all_day = all_day

            self.db.commit()
            self.db.refresh(external_event)

            logger.info(f"Updated event {external_event.id}")
            return external_event

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    def delete_event(self, event_id: UUID) -> None:
        """
        Delete an event from Google Calendar and local database.

        Args:
            event_id: The external event UUID
        """
        # Get the event
        stmt = select(ExternalEvent).where(ExternalEvent.id == event_id)
        external_event = self.db.execute(stmt).scalar_one_or_none()

        if not external_event:
            raise ValueError(f"Event {event_id} not found")

        if not external_event.external_event_id:
            # Event only exists locally, just delete from database
            self.db.delete(external_event)
            self.db.commit()
            logger.info(f"Deleted local event {event_id}")
            return

        # Get the calendar source and OAuth account
        calendar_source = external_event.calendar_source
        oauth_account = calendar_source.oauth_account
        google_service = GoogleCalendarService(oauth_account, self.db)

        try:
            # Delete from Google Calendar
            google_service.delete_event(
                calendar_id=calendar_source.external_calendar_id,
                event_id=external_event.external_event_id,
            )

            # Delete from local database
            self.db.delete(external_event)
            self.db.commit()

            logger.info(f"Deleted event {event_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    def get_events(
        self,
        user_id: UUID,
        start_min: Optional[datetime] = None,
        start_max: Optional[datetime] = None,
        calendar_source_id: Optional[UUID] = None,
    ) -> list[ExternalEvent]:
        """
        Get events for a user, optionally filtered by time range and calendar.

        Args:
            user_id: The user's UUID
            start_min: Minimum event start time
            start_max: Maximum event start time
            calendar_source_id: Optional calendar source to filter by

        Returns:
            List of ExternalEvent objects
        """
        # Build query
        stmt = select(ExternalEvent).join(
            CalendarSource,
            ExternalEvent.calendar_source_id == CalendarSource.id
        ).join(
            CalendarSource.oauth_account
        ).where(
            CalendarSource.oauth_account.has(user_id=user_id)
        )

        if calendar_source_id:
            stmt = stmt.where(ExternalEvent.calendar_source_id == calendar_source_id)

        if start_min:
            stmt = stmt.where(ExternalEvent.start_at >= start_min)

        if start_max:
            stmt = stmt.where(ExternalEvent.start_at <= start_max)

        stmt = stmt.order_by(ExternalEvent.start_at)

        events = self.db.execute(stmt).scalars().all()
        return list(events)
