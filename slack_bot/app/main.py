"""EPI Slack Bot — entry point.

Starts a Slack Bolt async app in Socket Mode so it can receive events
without exposing a public HTTP endpoint.

Required environment variables
-------------------------------
SLACK_BOT_TOKEN      — ``xoxb-...`` OAuth bot token.
SLACK_APP_TOKEN      — ``xapp-...`` app-level token for Socket Mode.
SLACK_SIGNING_SECRET — signing secret from the Slack app settings.
ANTHROPIC_API_KEY    — Anthropic API key for Claude.
BACKEND_URL          — EPI backend base URL (default ``http://backend:8000``).
EPI_API_KEY          — backend API key (single-tenant fallback).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from app.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        logger.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value


async def start() -> None:
    slack_bot_token = _require_env("SLACK_BOT_TOKEN")
    slack_app_token = _require_env("SLACK_APP_TOKEN")
    signing_secret = _require_env("SLACK_SIGNING_SECRET")

    # Validate that other required vars exist early so we fail fast.
    _require_env("ANTHROPIC_API_KEY")

    app = AsyncApp(token=slack_bot_token, signing_secret=signing_secret)
    register_handlers(app)

    handler = AsyncSocketModeHandler(app, slack_app_token)
    logger.info("EPI Slack bot starting in Socket Mode...")
    await handler.start_async()


def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
