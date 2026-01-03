"""
OAuth authentication router for Google Calendar integration.

This module handles the OAuth2 flow for connecting Google Calendar accounts.
"""

from datetime import datetime, timezone
from typing import Optional
import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from app.core.security import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.schemas.calendar import OAuthAccountResponse

router = APIRouter(prefix="/oauth", tags=["oauth"])
logger = logging.getLogger(__name__)
settings = get_settings()


class OAuthCallbackRequest(BaseModel):
    """OAuth callback data."""
    code: str
    state: Optional[str] = None


@router.get("/google/authorize")
async def google_authorize(
    user_id: str = Query(..., description="User ID from frontend"),
    db: Session = Depends(get_db),
):
    """
    Initiate the Google OAuth2 authorization flow.

    This endpoint redirects the user to Google's OAuth consent screen.
    After authorization, Google will redirect back to the callback endpoint.

    Args:
        user_id: User ID from frontend
        db: Database session

    Returns:
        Redirect to Google's OAuth authorization URL
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        )

    # Verify user exists
    from sqlalchemy import select
    stmt = select(User).where(User.id == user_id)
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build authorization URL
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent",
        "state": f"{state}:{user_id}",  # Include user ID in state
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    logger.info(f"Redirecting user {user_id} to Google OAuth")

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Handle the OAuth2 callback from Google.

    Google redirects here after the user authorizes the application.
    This endpoint exchanges the authorization code for access/refresh tokens.

    Args:
        code: Authorization code from Google
        state: State parameter for CSRF protection
        db: Database session

    Returns:
        Redirect to the application with success message
    """
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")

    # Extract user ID from state
    try:
        _, user_id = state.split(":", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for tokens
    import requests

    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
    )

    if token_response.status_code != 200:
        logger.error(f"Token exchange failed: {token_response.text}")
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    tokens = token_response.json()

    # Get user info from Google
    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    if user_info_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    user_info = user_info_response.json()
    google_user_id = user_info["id"]

    # Check if OAuth account already exists
    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == user_id,
        OAuthAccount.provider == "google",
        OAuthAccount.provider_account_id == google_user_id
    )
    oauth_account = db.execute(stmt).scalar_one_or_none()

    # Calculate token expiry
    expires_in = tokens.get("expires_in", 3600)
    token_expires_at = datetime.now(timezone.utc).timestamp() + expires_in

    if oauth_account:
        # Update existing
        oauth_account.access_token = tokens["access_token"]
        oauth_account.refresh_token = tokens.get("refresh_token")
        oauth_account.token_expires_at = datetime.fromtimestamp(token_expires_at, tz=timezone.utc)
        oauth_account.scopes = {"calendar": True}
    else:
        # Create new
        oauth_account = OAuthAccount(
            user_id=user_id,
            provider="google",
            provider_account_id=google_user_id,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expires_at=datetime.fromtimestamp(token_expires_at, tz=timezone.utc),
            scopes={"calendar": True},
        )
        db.add(oauth_account)

    db.commit()

    logger.info(f"Successfully connected Google Calendar for user {user_id}")

    # Redirect back to frontend
    return RedirectResponse(url="http://localhost:3000/calendar?success=true")


@router.post("/google/disconnect")
async def google_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect a user's Google Calendar account.

    This removes the OAuth connection and all associated calendar data.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        Success message
    """
    from sqlalchemy import select

    # Find all Google OAuth accounts for this user
    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == current_user.id,
        OAuthAccount.provider == "google"
    )
    oauth_accounts = db.execute(stmt).scalars().all()

    if not oauth_accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connection found"
        )

    # Delete all OAuth accounts (cascade will delete calendar_sources and events)
    for account in oauth_accounts:
        db.delete(account)

    db.commit()

    logger.info(f"Disconnected {len(oauth_accounts)} Google account(s) for user {current_user.id}")

    return {
        "message": "Google Calendar disconnected successfully",
        "accounts_removed": len(oauth_accounts)
    }


@router.get("/google/status", response_model=list[OAuthAccountResponse])
async def google_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the status of the user's Google Calendar connections.

    Args:
        current_user: The authenticated user
        db: Database session

    Returns:
        List of connected Google OAuth accounts
    """
    from sqlalchemy import select

    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == current_user.id,
        OAuthAccount.provider == "google"
    )
    oauth_accounts = db.execute(stmt).scalars().all()

    return oauth_accounts
