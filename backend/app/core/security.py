"""
Authentication and security utilities.

Handles user session verification and authentication for protected endpoints.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    """
    Identify the current user via Authorization header (from frontend).

    Args:
        request: FastAPI request object containing headers
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    # Check for Authorization header with user ID
    user_id_header = request.headers.get("Authorization")

    if not user_id_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - Authorization header missing",
        )

    # Convert string to UUID for database query
    try:
        user_id = UUID(user_id_header)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
