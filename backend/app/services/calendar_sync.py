"""
Calendar synchronization service.

This module handles syncing calendars and events from Google Calendar
to the local database for caching and conflict detection.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.oauth_account import OAuthAccount
from app.models.calendar_source import CalendarSource
from app.models.external_event import ExternalEvent
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class CalendarSyncService:
    """Service for synchronizing calendars and events."""

    def __init__(self, db: Session):
        """
        Initialize the sync service.

        Args:
            db: Database session
        """
        self.db = db

    def sync_user_calendars(self, user_id: str) -> tuple[int, int]:
        """
        Sync all calendars for a user from their connected Google accounts.

        Args:
            user_id: The user's UUID

        Returns:
            Tuple of (calendars_synced, events_synced)
        """
        # Get all Google OAuth accounts for this user
        stmt = select(OAuthAccount).where(
            OAuthAccount.user_id == user_id,
            OAuthAccount.provider == "google"
        )
        oauth_accounts = self.db.execute(stmt).scalars().all()

        total_calendars = 0
        total_events = 0

        for oauth_account in oauth_accounts:
            try:
                calendars_synced, events_synced = self._sync_account_calendars(oauth_account)
                total_calendars += calendars_synced
                total_events += events_synced
            except Exception as e:
                logger.error(f"Error syncing calendars for account {oauth_account.id}: {e}")
                continue

        return total_calendars, total_events

    def _sync_account_calendars(self, oauth_account: OAuthAccount) -> tuple[int, int]:
        """
        Sync calendars for a specific OAuth account.

        Args:
            oauth_account: The OAuth account to sync

        Returns:
            Tuple of (calendars_synced, events_synced)
        """
        google_service = GoogleCalendarService(oauth_account, self.db)

        # Fetch calendars from Google
        try:
            google_calendars = google_service.list_calendars()
        except Exception as e:
            logger.error(f"Failed to fetch calendars for account {oauth_account.id}: {e}")
            raise

        calendars_synced = 0
        total_events = 0

        for gcal in google_calendars:
            try:
                # Sync or create calendar source
                calendar_source = self._sync_calendar_source(oauth_account, gcal)
                calendars_synced += 1

                # Sync events for this calendar
                events_synced = self._sync_calendar_events(
                    calendar_source,
                    google_service
                )
                total_events += events_synced

            except Exception as e:
                logger.error(f"Error syncing calendar {gcal.get('id')}: {e}")
                continue

        self.db.commit()
        return calendars_synced, total_events

    def _sync_calendar_source(
        self,
        oauth_account: OAuthAccount,
        google_calendar: dict
    ) -> CalendarSource:
        """
        Sync or create a calendar source from Google Calendar data.

        Args:
            oauth_account: The OAuth account
            google_calendar: Google Calendar API calendar object

        Returns:
            The synced CalendarSource
        """
        external_id = google_calendar["id"]

        # Check if calendar source already exists
        stmt = select(CalendarSource).where(
            CalendarSource.oauth_account_id == oauth_account.id,
            CalendarSource.external_calendar_id == external_id
        )
        calendar_source = self.db.execute(stmt).scalar_one_or_none()

        if calendar_source:
            # Update existing
            calendar_source.name = google_calendar.get("summary", "Unnamed Calendar")
            calendar_source.is_primary = google_calendar.get("primary", False)
            calendar_source.timezone = google_calendar.get("timeZone", "UTC")
        else:
            # Create new
            calendar_source = CalendarSource(
                oauth_account_id=oauth_account.id,
                external_calendar_id=external_id,
                name=google_calendar.get("summary", "Unnamed Calendar"),
                is_primary=google_calendar.get("primary", False),
                timezone=google_calendar.get("timeZone", "UTC"),
            )
            self.db.add(calendar_source)
            self.db.flush()  # Get the ID

        logger.info(f"Synced calendar source: {calendar_source.name}")
        return calendar_source

    def _sync_calendar_events(
        self,
        calendar_source: CalendarSource,
        google_service: GoogleCalendarService,
        days_back: int = 30,
        days_forward: int = 90,
    ) -> int:
        """
        Sync events for a calendar source.

        Args:
            calendar_source: The calendar source to sync
            google_service: Google Calendar service instance
            days_back: How many days in the past to sync
            days_forward: How many days in the future to sync

        Returns:
            Number of events synced
        """
        # Calculate time range
        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=days_back)
        time_max = now + timedelta(days=days_forward)

        try:
            # Fetch events from Google
            events_result = google_service.get_events(
                calendar_id=calendar_source.external_calendar_id,
                time_min=time_min,
                time_max=time_max,
            )
            google_events = events_result.get("items", [])

            events_synced = 0

            for gevent in google_events:
                try:
                    self._sync_event(calendar_source, gevent)
                    events_synced += 1
                except Exception as e:
                    logger.error(f"Error syncing event {gevent.get('id')}: {e}")
                    continue

            logger.info(f"Synced {events_synced} events for calendar {calendar_source.name}")
            return events_synced

        except Exception as e:
            logger.error(f"Failed to sync events for calendar {calendar_source.id}: {e}")
            raise

    def _sync_event(self, calendar_source: CalendarSource, google_event: dict) -> ExternalEvent:
        """
        Sync or create an external event from Google Calendar event data.

        Args:
            calendar_source: The calendar source
            google_event: Google Calendar API event object

        Returns:
            The synced ExternalEvent
        """
        external_event_id = google_event.get("id")

        # Parse start and end times
        start_data = google_event.get("start", {})
        end_data = google_event.get("end", {})

        # Check if it's an all-day event
        all_day = "date" in start_data

        if all_day:
            # All-day events use date format
            start_at = datetime.fromisoformat(start_data["date"]).replace(tzinfo=timezone.utc)
            end_at = datetime.fromisoformat(end_data["date"]).replace(tzinfo=timezone.utc)
        else:
            # Timed events use dateTime format
            start_at = datetime.fromisoformat(start_data.get("dateTime", ""))
            end_at = datetime.fromisoformat(end_data.get("dateTime", ""))

        # Check if event already exists
        stmt = select(ExternalEvent).where(
            ExternalEvent.calendar_source_id == calendar_source.id,
            ExternalEvent.external_event_id == external_event_id
        )
        external_event = self.db.execute(stmt).scalar_one_or_none()

        if external_event:
            # Update existing
            external_event.title = google_event.get("summary", "Untitled Event")
            external_event.description = google_event.get("description")
            external_event.location = google_event.get("location")
            external_event.start_at = start_at
            external_event.end_at = end_at
            external_event.all_day = all_day
            external_event.status = google_event.get("status", "confirmed")
        else:
            # Create new
            external_event = ExternalEvent(
                calendar_source_id=calendar_source.id,
                external_event_id=external_event_id,
                title=google_event.get("summary", "Untitled Event"),
                description=google_event.get("description"),
                location=google_event.get("location"),
                start_at=start_at,
                end_at=end_at,
                all_day=all_day,
                source="imported",
                status=google_event.get("status", "confirmed"),
            )
            self.db.add(external_event)

        return external_event

    def sync_calendar_source(self, calendar_source_id: str) -> int:
        """
        Sync events for a specific calendar source.

        Args:
            calendar_source_id: The calendar source UUID

        Returns:
            Number of events synced
        """
        stmt = select(CalendarSource).where(CalendarSource.id == calendar_source_id)
        calendar_source = self.db.execute(stmt).scalar_one_or_none()

        if not calendar_source:
            raise ValueError(f"Calendar source {calendar_source_id} not found")

        # Get the OAuth account
        oauth_account = calendar_source.oauth_account

        # Create Google service
        google_service = GoogleCalendarService(oauth_account, self.db)

        # Sync events
        events_synced = self._sync_calendar_events(calendar_source, google_service)

        self.db.commit()
        return events_synced
