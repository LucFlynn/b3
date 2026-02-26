"""Slack event handlers for the EPI bot.

Handles ``app_mention`` events (when the bot is @-mentioned in a channel)
and ``message`` events in DMs. Each handler resolves the agency context
from the Slack workspace ID, then delegates to the Claude client.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from slack_bolt.async_app import AsyncApp

from app.claude_client import ClaudeEPIClient
from app.data_fetcher import EPIBackendClient

logger = logging.getLogger(__name__)

# Workspace-to-API-key mapping.  In production each agency installs the
# Slack app into their own workspace.  The mapping is read from env vars
# of the form  AGENCY_MAP_<WORKSPACE_ID>=<api_key>
# e.g.  AGENCY_MAP_T01ABC123=epi_abc123...
#
# If only a single workspace is served, the fallback ``EPI_API_KEY`` is used.

_MENTION_RE = re.compile(r"<@[A-Z0-9]+>\s*")


def _strip_mention(text: str) -> str:
    """Remove the ``<@BOTID>`` prefix so Claude gets the actual question."""
    return _MENTION_RE.sub("", text).strip()


def _api_key_for_workspace(workspace_id: str) -> str:
    """Resolve the EPI backend API key for a given Slack workspace."""
    key = os.environ.get(f"AGENCY_MAP_{workspace_id}")
    if key:
        return key
    # Fallback: single-tenant mode
    fallback = os.environ.get("EPI_API_KEY", "")
    if not fallback:
        raise RuntimeError(
            f"No API key configured for workspace {workspace_id}. "
            "Set AGENCY_MAP_<WORKSPACE_ID> or EPI_API_KEY in the environment."
        )
    return fallback


def _build_claude_client(workspace_id: str) -> ClaudeEPIClient:
    """Construct a Claude client wired to the correct agency backend."""
    api_key = _api_key_for_workspace(workspace_id)
    backend_url = os.environ.get("BACKEND_URL", "http://backend:8000")
    anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]

    backend = EPIBackendClient(base_url=backend_url, api_key=api_key)
    return ClaudeEPIClient(anthropic_api_key=anthropic_api_key, backend_client=backend)


def register_handlers(app: AsyncApp) -> None:
    """Wire Slack event handlers onto *app*."""

    @app.event("app_mention")
    async def handle_mention(event: dict[str, Any], say: Any, context: dict[str, Any]) -> None:
        """Respond when the bot is @-mentioned in a channel."""
        workspace_id = context.get("team_id", event.get("team"))
        user_text = _strip_mention(event.get("text", ""))
        if not user_text:
            await say("Hey! Ask me anything about your leads, attribution data, or tracked sites.")
            return

        thread_ts = event.get("thread_ts") or event.get("ts")
        try:
            claude = _build_claude_client(workspace_id)
            answer = await claude.ask(user_text)
            await say(text=answer, thread_ts=thread_ts)
        except Exception:
            logger.exception("Error handling mention from workspace %s", workspace_id)
            await say(
                text="Sorry, something went wrong while processing your request. Please try again shortly.",
                thread_ts=thread_ts,
            )

    @app.event("message")
    async def handle_dm(event: dict[str, Any], say: Any, context: dict[str, Any]) -> None:
        """Respond to direct messages sent to the bot."""
        # Ignore bot messages, message_changed subtypes, etc.
        if event.get("subtype"):
            return

        # Only handle DMs (channel type "im")
        channel_type = event.get("channel_type", "")
        if channel_type != "im":
            return

        workspace_id = context.get("team_id", event.get("team"))
        user_text = (event.get("text") or "").strip()
        if not user_text:
            return

        thread_ts = event.get("thread_ts") or event.get("ts")
        try:
            claude = _build_claude_client(workspace_id)
            answer = await claude.ask(user_text)
            await say(text=answer, thread_ts=thread_ts)
        except Exception:
            logger.exception("Error handling DM from workspace %s", workspace_id)
            await say(
                text="Sorry, something went wrong while processing your request. Please try again shortly.",
                thread_ts=thread_ts,
            )
