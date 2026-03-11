"""Google Ads OAuth flow — connect/disconnect/list Google Ads accounts."""

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
from app.models.google_ads_connection import GoogleAdsConnection
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.security import get_current_user, encrypt_pii, decrypt_pii

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google-ads", tags=["google-ads"])

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_ADS_SCOPE = "https://www.googleapis.com/auth/adwords"


@router.get("/auth-url")
async def get_auth_url(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate the Google OAuth authorization URL with a random state nonce."""
    state = secrets.token_urlsafe(32)
    nonce = OAuthState(
        state=state,
        user_id=user.clerk_user_id or str(user.id),
        provider="google",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(nonce)
    await db.flush()

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_ADS_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": url}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Google. Exchange code for tokens."""
    # Validate state nonce
    result = await db.execute(
        select(OAuthState).where(
            OAuthState.state == state,
            OAuthState.provider == "google",
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

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if resp.status_code != 200:
        logger.error("Google token exchange failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    token_data = resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token received. Please try connecting again.",
        )

    # Fetch accessible Google Ads customer accounts
    accounts = await _list_accessible_customers(refresh_token)

    # Store the connection (tokens encrypted)
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if len(accounts) == 1:
        # Auto-connect single account
        acct = accounts[0]
        connection = GoogleAdsConnection(
            user_id=user_id,
            google_ads_customer_id=acct["customer_id"],
            account_name=acct.get("descriptive_name", ""),
            access_token_encrypted=encrypt_pii(access_token),
            refresh_token_encrypted=encrypt_pii(refresh_token),
            token_expiry=token_expiry,
        )
        db.add(connection)
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?google_ads=connected",
            status_code=302,
        )
    elif len(accounts) == 0:
        # No accounts found (developer token may lack access) — store tokens anyway
        connection = GoogleAdsConnection(
            user_id=user_id,
            access_token_encrypted=encrypt_pii(access_token),
            refresh_token_encrypted=encrypt_pii(refresh_token),
            token_expiry=token_expiry,
            status="active",
            account_name="Google Ads",
        )
        db.add(connection)
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?google_ads=connected",
            status_code=302,
        )
    else:
        # Multiple accounts — store as pending, let user pick
        connection = GoogleAdsConnection(
            user_id=user_id,
            access_token_encrypted=encrypt_pii(access_token),
            refresh_token_encrypted=encrypt_pii(refresh_token),
            token_expiry=token_expiry,
            status="pending_selection",
        )
        db.add(connection)
        await db.flush()
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?google_ads=select&connection_id={connection.id}",
            status_code=302,
        )


@router.get("/pending-accounts/{connection_id}")
async def pending_accounts(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch available Google Ads accounts for a pending connection."""
    from uuid import UUID

    result = await db.execute(
        select(GoogleAdsConnection).where(
            GoogleAdsConnection.id == UUID(connection_id),
            GoogleAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
            GoogleAdsConnection.status == "pending_selection",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    refresh_token = decrypt_pii(connection.refresh_token_encrypted)
    accounts = await _list_accessible_customers(refresh_token)
    return {"connection_id": str(connection.id), "accounts": accounts}


@router.post("/select-account")
async def select_account(
    connection_id: str = Query(...),
    customer_id: str = Query(...),
    account_name: str = Query(""),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select which Google Ads account to connect (when user has multiple)."""
    from uuid import UUID

    result = await db.execute(
        select(GoogleAdsConnection).where(
            GoogleAdsConnection.id == UUID(connection_id),
            GoogleAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
            GoogleAdsConnection.status == "pending_selection",
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.google_ads_customer_id = customer_id
    connection.account_name = account_name
    connection.status = "active"
    db.add(connection)

    return {"status": "connected", "customer_id": customer_id}


@router.get("/connections")
async def list_connections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all connected Google Ads accounts for the current user."""
    user_id = user.clerk_user_id or str(user.id)
    result = await db.execute(
        select(GoogleAdsConnection).where(
            GoogleAdsConnection.user_id == user_id,
            GoogleAdsConnection.status == "active",
        )
    )
    connections = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "customer_id": c.google_ads_customer_id,
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
    """Disconnect a Google Ads account — revokes token and marks as revoked."""
    from uuid import UUID

    result = await db.execute(
        select(GoogleAdsConnection).where(
            GoogleAdsConnection.id == UUID(connection_id),
            GoogleAdsConnection.user_id == (user.clerk_user_id or str(user.id)),
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Revoke the token at Google
    if connection.refresh_token_encrypted:
        try:
            refresh_token = decrypt_pii(connection.refresh_token_encrypted)
            async with httpx.AsyncClient() as client:
                await client.post(GOOGLE_REVOKE_URL, params={"token": refresh_token})
        except Exception as e:
            logger.warning("Failed to revoke Google token: %s", e)

    # Clear tokens and mark as revoked
    connection.access_token_encrypted = None
    connection.refresh_token_encrypted = None
    connection.status = "revoked"
    db.add(connection)

    return {"status": "disconnected"}


async def get_valid_access_token(connection: GoogleAdsConnection, db: AsyncSession) -> str:
    """Get a valid access token, refreshing if expired. Returns the access token string."""
    now = datetime.now(timezone.utc)

    # Check if current token is still valid (with 5-min buffer)
    if connection.token_expiry and connection.token_expiry > now + timedelta(minutes=5):
        if connection.access_token_encrypted:
            return decrypt_pii(connection.access_token_encrypted)

    # Need to refresh
    if not connection.refresh_token_encrypted:
        connection.status = "expired"
        db.add(connection)
        raise HTTPException(status_code=401, detail="Google Ads connection expired. Please reconnect.")

    refresh_token = decrypt_pii(connection.refresh_token_encrypted)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

    if resp.status_code != 200:
        logger.error("Google token refresh failed: %s %s", resp.status_code, resp.text)
        connection.status = "expired"
        db.add(connection)
        raise HTTPException(status_code=401, detail="Google Ads connection expired. Please reconnect.")

    token_data = resp.json()
    new_access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 3600)

    connection.access_token_encrypted = encrypt_pii(new_access_token)
    connection.token_expiry = now + timedelta(seconds=expires_in)
    connection.last_used_at = now
    db.add(connection)

    return new_access_token


async def _list_accessible_customers(refresh_token: str) -> list[dict]:
    """Get a fresh access token from the refresh token, then list accounts via REST."""
    # Step 1: Get a fresh access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if token_resp.status_code != 200:
        logger.error("Failed to refresh token for account listing: %s", token_resp.text)
        return []

    access_token = token_resp.json()["access_token"]

    # Step 2: Use Google Ads REST API v17
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": settings.google_ads_developer_token,
    }
    login_cid = settings.google_ads_login_customer_id
    if login_cid:
        headers["login-customer-id"] = login_cid

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://googleads.googleapis.com/v17/customers:listAccessibleCustomers",
            headers=headers,
        )

    if resp.status_code != 200:
        logger.error("Failed to list Google Ads customers: %s %s", resp.status_code, resp.text)
        return []

    data = resp.json()
    resource_names = data.get("resourceNames", [])

    accounts = []
    for resource_name in resource_names:
        customer_id = resource_name.split("/")[-1]
        # Get account details via GAQL search
        search_url = f"https://googleads.googleapis.com/v17/customers/{customer_id}/googleAds:searchStream"
        query_body = {"query": "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"}
        async with httpx.AsyncClient() as client:
            detail_resp = await client.post(search_url, headers=headers, json=query_body)

        if detail_resp.status_code == 200:
            results = detail_resp.json()
            if results and len(results) > 0:
                rows = results[0].get("results", [])
                if rows:
                    name = rows[0].get("customer", {}).get("descriptiveName", "")
                    accounts.append({"customer_id": customer_id, "descriptive_name": name})
                    continue
        accounts.append({"customer_id": customer_id, "descriptive_name": ""})

    return accounts
