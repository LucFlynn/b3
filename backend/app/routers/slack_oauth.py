"""Slack OAuth V2 flow — install the EPI Slack bot on customer workspaces."""

import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.slack_connection import SlackConnection
from app.models.user import User
from app.models.agency import Agency
from app.security import get_current_user, encrypt_pii, decrypt_pii

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/slack", tags=["slack"])

# Slack OAuth V2 endpoints
SLACK_AUTH_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
SLACK_REVOKE_URL = "https://slack.com/api/auth.revoke"

# Bot scopes requested during install
BOT_SCOPES = "chat:write,channels:read,groups:read,im:read"


@router.get("/install-url")
async def get_install_url(user: User = Depends(get_current_user)):
    """Generate the Slack OAuth install URL."""
    if not settings.slack_client_id:
        raise HTTPException(status_code=500, detail="Slack OAuth not configured")

    params = {
        "client_id": settings.slack_client_id,
        "redirect_uri": settings.slack_redirect_uri,
        "scope": BOT_SCOPES,
        "state": user.clerk_user_id or str(user.id),
    }
    url = f"{SLACK_AUTH_URL}?{urlencode(params)}"
    return {"install_url": url}


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Slack. Exchange code for bot token."""
    # Exchange authorization code for bot token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SLACK_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_oauth_client_secret,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )

    if resp.status_code != 200:
        logger.error("Slack token exchange HTTP failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    data = resp.json()
    if not data.get("ok"):
        logger.error("Slack token exchange error: %s", data.get("error"))
        raise HTTPException(status_code=400, detail=f"Slack error: {data.get('error')}")

    access_token = data.get("access_token", "")
    team = data.get("team", {})
    team_id = team.get("id", "")
    team_name = team.get("name", "")
    bot_user_id = data.get("bot_user_id", "")

    # Incoming webhook channel (if provided by Slack)
    incoming_webhook = data.get("incoming_webhook", {})
    channel_id = incoming_webhook.get("channel_id", "")
    channel_name = incoming_webhook.get("channel", "")

    # Store the connection with encrypted bot token
    connection = SlackConnection(
        user_id=state,
        workspace_id=team_id,
        workspace_name=team_name,
        channel_id=channel_id or None,
        channel_name=channel_name or None,
        bot_token_encrypted=encrypt_pii(access_token),
        bot_user_id=bot_user_id,
    )
    db.add(connection)

    # Update the user's Agency with workspace_id
    if state and team_id:
        from app.models.user import User as UserModel

        result = await db.execute(
            select(UserModel).where(UserModel.clerk_user_id == state)
        )
        user = result.scalar_one_or_none()
        if user and user.agency_id:
            result = await db.execute(
                select(Agency).where(Agency.id == user.agency_id)
            )
            agency = result.scalar_one_or_none()
            if agency:
                agency.slack_workspace_id = team_id
                if channel_id:
                    agency.slack_channel_id = channel_id
                db.add(agency)

    return RedirectResponse(
        url=f"{settings.frontend_url}/dashboard?slack=connected",
        status_code=302,
    )


@router.get("/connections")
async def list_connections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active Slack connections for the current user."""
    user_id = user.clerk_user_id or str(user.id)
    result = await db.execute(
        select(SlackConnection).where(
            SlackConnection.user_id == user_id,
            SlackConnection.status == "active",
        )
    )
    connections = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "workspace_id": c.workspace_id,
            "workspace_name": c.workspace_name,
            "channel_id": c.channel_id,
            "channel_name": c.channel_name,
            "bot_user_id": c.bot_user_id,
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
    """Disconnect a Slack workspace — revokes bot token and marks as revoked."""
    from uuid import UUID

    result = await db.execute(
        select(SlackConnection).where(
            SlackConnection.id == UUID(connection_id),
            SlackConnection.user_id == (user.clerk_user_id or str(user.id)),
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Revoke the bot token at Slack
    if connection.bot_token_encrypted:
        try:
            bot_token = decrypt_pii(connection.bot_token_encrypted)
            async with httpx.AsyncClient() as client:
                await client.post(
                    SLACK_REVOKE_URL,
                    headers={"Authorization": f"Bearer {bot_token}"},
                )
        except Exception as e:
            logger.warning("Failed to revoke Slack token: %s", e)

    # Clear token and mark as revoked
    connection.bot_token_encrypted = None
    connection.status = "revoked"
    db.add(connection)

    return {"status": "disconnected"}
