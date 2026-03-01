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
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

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


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","service":"epi-slackbot"}')

    def log_message(self, format, *args):
        pass


def _start_health_server():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    logger.info("Health server listening on port %d", port)
    server.serve_forever()


async def start() -> None:
    # Start health server first so Cloud Run sees the port open
    threading.Thread(target=_start_health_server, daemon=True).start()

    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    slack_app_token = os.environ.get("SLACK_APP_TOKEN", "").strip()
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "").strip()
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if not all([slack_bot_token, slack_app_token, signing_secret, anthropic_key]) or slack_bot_token == "placeholder":
        logger.warning("Slack credentials not configured — bot idle, health server running")
        # Keep alive for Cloud Run health checks
        while True:
            await asyncio.sleep(3600)

    app = AsyncApp(token=slack_bot_token, signing_secret=signing_secret)
    register_handlers(app)

    handler = AsyncSocketModeHandler(app, slack_app_token)
    logger.info("EPI Slack bot starting in Socket Mode...")
    await handler.start_async()


def main() -> None:
    asyncio.run(start())


if __name__ == "__main__":
    main()
