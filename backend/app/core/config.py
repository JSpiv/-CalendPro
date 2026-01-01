"""
Application settings and configuration.

This module centralizes configuration so both the FastAPI app and
Alembic migrations can read database settings from the same place.
"""

from functools import lru_cache
import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime application settings."""

    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        # Do not hard-code a default here; rely on environment configuration.
        # Prefer a backend-specific variable so other tools (e.g. Prisma) can use
        # their own DB URL without interfering with Alembic/SQLAlchemy.
        database_url = os.getenv("BACKEND_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "BACKEND_DATABASE_URL (or DATABASE_URL) environment variable is not set"
            )
        return cls(database_url=database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached access to application settings.

    Alembic and the FastAPI app should both import and use this helper.
    """

    return Settings.from_env()
