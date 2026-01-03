"""
Google Calendar API service wrapper.

This module provides a clean interface to interact with the Google Calendar API,
handling authentication, token refresh, and API calls.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import logging

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.models.oauth_account import OAuthAccount
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    def __init__(self, oauth_account: OAuthAccount, db: Session):
        """
        Initialize the Google Calendar service.

        Args:
            oauth_account: The OAuthAccount with Google credentials
            db: Database session for token updates
        """
        self.oauth_account = oauth_account
        self.db = db
        self._service = None
        self.settings = get_settings()

    def _get_credentials(self) -> Credentials:
        """Build Google OAuth2 credentials from the OAuthAccount."""
        return Credentials(
            token=self.oauth_account.access_token,
            refresh_token=self.oauth_account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
        )

    def _get_service(self):
        """Get or create the Google Calendar API service."""
        if self._service is None:
            credentials = self._get_credentials()
            self._service = build("calendar", "v3", credentials=credentials)
        return self._service

    def _refresh_token_if_needed(self):
        """Check if token is expired and refresh if necessary."""
        if self.oauth_account.token_expires_at:
            now = datetime.now(timezone.utc)
            # Refresh 5 minutes before expiry to be safe
            if now >= self.oauth_account.token_expires_at - timedelta(minutes=5):
                logger.info(f"Token expired for account {self.oauth_account.id}, refreshing...")

                if not self.oauth_account.refresh_token:
                    logger.error(f"No refresh token available for account {self.oauth_account.id}")
                    raise ValueError("No refresh token available. User must re-authenticate.")

                try:
                    import requests
                    from app.core.config import get_settings

                    settings = get_settings()

                    # Request new access token
                    response = requests.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": settings.google_client_id,
                            "client_secret": settings.google_client_secret,
                            "refresh_token": self.oauth_account.refresh_token,
                            "grant_type": "refresh_token",
                        }
                    )

                    if response.status_code != 200:
                        logger.error(f"Failed to refresh token: {response.text}")
                        raise ValueError(f"Failed to refresh token: {response.text}")

                    tokens = response.json()

                    # Update the oauth_account with new tokens
                    self.oauth_account.access_token = tokens["access_token"]
                    expires_in = tokens.get("expires_in", 3600)
                    self.oauth_account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                    # Note: refresh_token usually doesn't change, but update if provided
                    if "refresh_token" in tokens:
                        self.oauth_account.refresh_token = tokens["refresh_token"]

                    # Commit to database
                    self.db.commit()
                    self.db.refresh(self.oauth_account)

                    # Clear cached credentials/service so they get rebuilt with new token
                    self._service = None

                    logger.info(f"Successfully refreshed token for account {self.oauth_account.id}")

                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    raise

    def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars for the authenticated user.

        Returns:
            List of calendar dictionaries from Google Calendar API
        """
        try:
            self._refresh_token_if_needed()
            service = self._get_service()

            calendar_list = service.calendarList().list().execute()
            return calendar_list.get("items", [])

        except HttpError as e:
            logger.error(f"Error listing calendars: {e}")
            raise

    def get_events(
        self,
        calendar_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        sync_token: Optional[str] = None,
        max_results: int = 250,
    ) -> Dict[str, Any]:
        """
        Get events from a specific calendar.

        Args:
            calendar_id: The Google Calendar ID
            time_min: Minimum event start time (inclusive)
            time_max: Maximum event start time (exclusive)
            sync_token: Token for incremental sync
            max_results: Maximum number of events to return

        Returns:
            Dictionary with 'items' (list of events) and optional 'nextSyncToken'
        """
        try:
            self._refresh_token_if_needed()
            service = self._get_service()

            params: Dict[str, Any] = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "singleEvents": True,  # Expand recurring events
                "orderBy": "startTime",
            }

            if sync_token:
                # Incremental sync
                params["syncToken"] = sync_token
            else:
                # Full sync with time range
                if time_min:
                    params["timeMin"] = time_min.isoformat()
                if time_max:
                    params["timeMax"] = time_max.isoformat()

            events_result = service.events().list(**params).execute()
            return events_result

        except HttpError as e:
            logger.error(f"Error fetching events from calendar {calendar_id}: {e}")
            raise

    def create_event(
        self,
        calendar_id: str,
        title: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new event in Google Calendar.

        Args:
            calendar_id: The Google Calendar ID
            title: Event title
            start: Event start time
            end: Event end time
            description: Event description
            location: Event location
            all_day: Whether this is an all-day event

        Returns:
            The created event data from Google Calendar
        """
        try:
            self._refresh_token_if_needed()
            service = self._get_service()

            event_body: Dict[str, Any] = {
                "summary": title,
            }

            if all_day:
                # All-day events use date format
                event_body["start"] = {"date": start.date().isoformat()}
                event_body["end"] = {"date": end.date().isoformat()}
            else:
                # Timed events use dateTime format
                event_body["start"] = {"dateTime": start.isoformat(), "timeZone": "UTC"}
                event_body["end"] = {"dateTime": end.isoformat(), "timeZone": "UTC"}

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location

            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()

            logger.info(f"Created event {event['id']} in calendar {calendar_id}")
            return event

        except HttpError as e:
            logger.error(f"Error creating event in calendar {calendar_id}: {e}")
            raise

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing event in Google Calendar.

        Args:
            calendar_id: The Google Calendar ID
            event_id: The Google event ID
            title: New event title
            start: New start time
            end: New end time
            description: New description
            location: New location
            all_day: Whether this is an all-day event

        Returns:
            The updated event data from Google Calendar
        """
        try:
            self._refresh_token_if_needed()
            service = self._get_service()

            # First, get the existing event
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Update only provided fields
            if title is not None:
                event["summary"] = title
            if description is not None:
                event["description"] = description
            if location is not None:
                event["location"] = location

            if start is not None and end is not None:
                if all_day:
                    event["start"] = {"date": start.date().isoformat()}
                    event["end"] = {"date": end.date().isoformat()}
                else:
                    event["start"] = {"dateTime": start.isoformat(), "timeZone": "UTC"}
                    event["end"] = {"dateTime": end.isoformat(), "timeZone": "UTC"}

            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated event {event_id} in calendar {calendar_id}")
            return updated_event

        except HttpError as e:
            logger.error(f"Error updating event {event_id}: {e}")
            raise

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        """
        Delete an event from Google Calendar.

        Args:
            calendar_id: The Google Calendar ID
            event_id: The Google event ID
        """
        try:
            self._refresh_token_if_needed()
            service = self._get_service()

            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            logger.info(f"Deleted event {event_id} from calendar {calendar_id}")

        except HttpError as e:
            logger.error(f"Error deleting event {event_id}: {e}")
            raise
