"""Meta Ads OAuth flow — connect/disconnect/list Meta Ads accounts."""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.meta_ads_connection import MetaAdsConnection
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.security import get_current_user, encrypt_pii, decrypt_pii

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta-ads", tags=["meta-ads"])

# Meta/Facebook OAuth endpoints
META_AUTH_URL = "https://www.facebook.com/v21.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
META_SCOPES = "ads_read,ads_management"


@router.get("/auth-url")
async def get_auth_url(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate the Meta OAuth authorization URL with a random state nonce."""
    state = secrets.token_urlsafe(32)
    nonce = OAuthState(
        state=state,
        user_id=user.clerk_user_id or str(user.id),
        provider="meta",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(nonce)
    await db.flush()

    params = {
        "client_id": settings.meta_client_id,
        "redirect_uri": settings.meta_redirect_uri,
        "response_type": "code",
        "scope": META_SCOPES,
        "state": state,
    }
    url = f"{META_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": url}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Meta. Exchange code for tokens."""
    # Validate state nonce
    result = await db.execute(
        select(OAuthState).where(
            OAuthState.state == state,
            OAuthState.provider == "meta",
        )
    )
    nonce = result.scalar_one_or_none()
    if not nonce or nonce.expires_at < datetime.now(timezone.utc):
        if nonce:
            await db.delete(nonce)
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    user_id = nonce.user_id
    await db.delete(nonce)
    await db.flush()

    # Step 1: Exchange authorization code for short-lived token
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            META_TOKEN_URL,
            params={
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "redirect_uri": settings.meta_redirect_uri,
                "code": code,
            },
        )

    if resp.status_code != 200:
        logger.error("Meta token exchange failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    short_lived_data = resp.json()
    short_lived_token = short_lived_data["access_token"]

    # Step 2: Exchange short-lived token for long-lived token (~60 days)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            META_TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_client_id,
                "client_secret": settings.meta_client_secret,
                "fb_exchange_token": short_lived_token,
            },
        )

    if resp.status_code != 200:
        logger.error("Meta long-lived token exchange failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=400, detail="Failed to obtain long-lived token")

    token_data = resp.json()
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)  # default 60 days

    # Step 3: Fetch ad accounts
    accounts = await _list_ad_accounts(access_token)

    # Store the connection (token encrypted)
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if len(accounts) == 1:
        # Auto-connect single account
        acct = accounts[0]
        connection = MetaAdsConnection(
            user_id=user_id,
            meta_ads_account_id=acct["account_id"],
            account_name=acct.get("name", ""),
            access_token_encrypted=encrypt_pii(access_token),
            token_expiry=token_expiry,
        )
        db.add(connection)
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?meta_ads=connected",
            status_code=302,
        )
    elif len(accounts) == 0:
        # No accounts found — store token anyway
        connection = MetaAdsConnection(
            user_id=user_id,
            access_token_encrypted=encrypt_pii(access_token),
            token_expiry=token_expiry,
            status="active",
            account_name="Meta Ads",
        )
        db.add(connection)
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?meta_ads=connected",
            status_code=302,
        )
    else:
        # Multiple accounts — store as pending, let user pick
        connection = MetaAdsConnection(
            user_id=user_id,
            access_token_encrypted=encrypt_pii(access_token),
            token_expiry=token_expiry,
            status="pending_selection",
        )
        db.add(connection)
        await db.flush()
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?meta_ads=select&connection_id={connection.id}",
            status_code=302,
        )


@router.get("/pending-accounts/{connection_id}")
async def pending_accounts(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch available Meta ad accounts for a pending connection."""
    from uuid import UUID

    result = await db.execute(
        select(MetaAdsConnection).where(
            MetaAdsConnection.id == UUID(connection_id),
            MetaAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
            MetaAdsConnection.status == "pending_selection",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    access_token = decrypt_pii(connection.access_token_encrypted)
    accounts = await _list_ad_accounts(access_token)
    return {"connection_id": str(connection.id), "accounts": accounts}


@router.post("/select-account")
async def select_account(
    connection_id: str = Query(...),
    account_id: str = Query(...),
    account_name: str = Query(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select which Meta Ads account to connect (when user has multiple)."""
    from uuid import UUID

    result = await db.execute(
        select(MetaAdsConnection).where(
            MetaAdsConnection.id == UUID(connection_id),
            MetaAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
            MetaAdsConnection.status == "pending_selection",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.meta_ads_account_id = account_id
    connection.account_name = account_name
    connection.status = "active"
    db.add(connection)

    return {"status": "connected", "account_id": account_id}


@router.get("/connections")
async def list_connections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all connected Meta Ads accounts for the current user."""
    user_id = user.clerk_user_id or str(user.id)
    result = await db.execute(
        select(MetaAdsConnection).where(
            MetaAdsConnection.user_id == user_id,
            MetaAdsConnection.status == "active",
        )
    )
    connections = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "account_id": c.meta_ads_account_id,
            "account_name": c.account_name,
            "connected_at": c.connected_at.isoformat() if c.connected_at else None,
            "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
            "status": c.status,
        }
        for c in connections
    ]


@router.post("/disconnect/{connection_id}")
async def disconnect(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a Meta Ads account — clears token and marks as revoked."""
    from uuid import UUID

    result = await db.execute(
        select(MetaAdsConnection).where(
            MetaAdsConnection.id == UUID(connection_id),
            MetaAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Clear token and mark as revoked (Meta tokens expire naturally, no revoke endpoint needed)
    connection.access_token_encrypted = None
    connection.status = "revoked"
    db.add(connection)

    return {"status": "disconnected"}


async def get_valid_access_token(connection: MetaAdsConnection, db: AsyncSession) -> str:
    """Get a valid access token. Meta long-lived tokens last ~60 days and cannot be refreshed
    programmatically — user must re-authenticate when expired."""
    now = datetime.now(timezone.utc)

    # Check if token is still valid (with 1-day buffer for Meta's longer tokens)
    if connection.token_expiry and connection.token_expiry > now + timedelta(days=1):
        if connection.access_token_encrypted:
            token = decrypt_pii(connection.access_token_encrypted)
            connection.last_used_at = now
            db.add(connection)
            return token

    # Warn if token is close to expiration (within 7 days)
    if connection.token_expiry and connection.token_expiry > now:
        days_left = (connection.token_expiry - now).days
        if days_left <= 7:
            logger.warning(
                "Meta Ads token for user %s expires in %d days. Re-authentication required soon.",
                connection.user_id,
                days_left,
            )
        if connection.access_token_encrypted:
            token = decrypt_pii(connection.access_token_encrypted)
            connection.last_used_at = now
            db.add(connection)
            return token

    # Token is expired — cannot refresh, user must re-auth
    connection.status = "expired"
    db.add(connection)
    raise HTTPException(
        status_code=401,
        detail="Meta Ads token expired. Please reconnect your Meta Ads account.",
    )


async def _list_ad_accounts(access_token: str) -> list[dict]:
    """Fetch all ad accounts accessible to the authenticated user (with pagination)."""
    url = "https://graph.facebook.com/v21.0/me/adaccounts"
    params = {
        "fields": "name,account_id,account_status",
        "access_token": access_token,
        "limit": "100",
    }

    accounts = []
    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.error("Failed to list Meta ad accounts: %s %s", resp.status_code, resp.text)
                break

            data = resp.json()
            for acct in data.get("data", []):
                accounts.append({
                    "account_id": acct.get("account_id", ""),
                    "name": acct.get("name", ""),
                    "account_status": acct.get("account_status"),
                })

            # Follow pagination cursor
            url = data.get("paging", {}).get("next")
            params = {}  # next URL includes all params

    return accounts
