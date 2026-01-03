"""
API routers.

Routers handle HTTP requests/responses and delegate business logic to services.
"""

from app.routers import oauth, calendars, events, tasks

__all__ = [
    "oauth",
    "calendars",
    "events",
    "tasks",
]
