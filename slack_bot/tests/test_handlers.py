"""Tests for EPI Slack bot handlers and supporting logic."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.handlers import _strip_mention, _api_key_for_workspace, _build_claude_client


# ------------------------------------------------------------------
# _strip_mention
# ------------------------------------------------------------------

class TestStripMention:
    def test_removes_single_mention(self):
        assert _strip_mention("<@U12345> what are my leads?") == "what are my leads?"

    def test_removes_multiple_mentions(self):
        assert _strip_mention("<@U12345> <@U67890> hello") == "hello"

    def test_no_mention(self):
        assert _strip_mention("just a plain message") == "just a plain message"

    def test_empty_after_strip(self):
        assert _strip_mention("<@U12345>") == ""

    def test_whitespace_handling(self):
        assert _strip_mention("<@U12345>   show me stats  ") == "show me stats"


# ------------------------------------------------------------------
# _api_key_for_workspace
# ------------------------------------------------------------------

class TestApiKeyForWorkspace:
    def test_workspace_specific_key(self, monkeypatch):
        monkeypatch.setenv("AGENCY_MAP_T01ABC", "epi_workspace_key")
        assert _api_key_for_workspace("T01ABC") == "epi_workspace_key"

    def test_fallback_to_epi_api_key(self, monkeypatch):
        monkeypatch.delenv("AGENCY_MAP_T01ABC", raising=False)
        monkeypatch.setenv("EPI_API_KEY", "epi_fallback_key")
        assert _api_key_for_workspace("T01ABC") == "epi_fallback_key"

    def test_raises_when_no_key(self, monkeypatch):
        monkeypatch.delenv("AGENCY_MAP_T99ZZZ", raising=False)
        monkeypatch.delenv("EPI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="No API key configured"):
            _api_key_for_workspace("T99ZZZ")


# ------------------------------------------------------------------
# _build_claude_client
# ------------------------------------------------------------------

class TestBuildClaudeClient:
    def test_returns_client(self, monkeypatch):
        monkeypatch.setenv("EPI_API_KEY", "epi_test_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
        client = _build_claude_client("T01XYZ")
        assert client is not None
        assert client._backend._base_url == "http://localhost:8000"
        assert client._backend._api_key == "epi_test_key"


# ------------------------------------------------------------------
# Handler integration (mock Slack + Claude)
# ------------------------------------------------------------------

class TestHandlerIntegration:
    @pytest.mark.asyncio
    async def test_mention_handler_calls_claude_and_responds(self, monkeypatch):
        monkeypatch.setenv("EPI_API_KEY", "epi_test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")

        mock_ask = AsyncMock(return_value="You have 42 leads total.")

        with patch("app.handlers._build_claude_client") as mock_build:
            mock_client = MagicMock()
            mock_client.ask = mock_ask
            mock_build.return_value = mock_client

            from app.handlers import handle_mention

            # Unwrap the inner function from Slack's decorator.
            # register_handlers wraps it, but we imported the raw function
            # via the module-level name used inside register_handlers.
            # Since register_handlers uses a closure, we need to call the
            # handler function that was defined inside register_handlers.
            # For this test we re-import after patching.
            from app.handlers import register_handlers

            app_mock = MagicMock()
            captured_handlers: dict = {}

            def capture_event(event_type):
                def decorator(fn):
                    captured_handlers[event_type] = fn
                    return fn
                return decorator

            app_mock.event = capture_event
            register_handlers(app_mock)

            mention_handler = captured_handlers["app_mention"]

            say = AsyncMock()
            event = {
                "text": "<@U0BOT> how many leads do I have?",
                "ts": "1234567890.123456",
                "team": "T01WORKSPACE",
            }
            context = {"team_id": "T01WORKSPACE"}

            await mention_handler(event=event, say=say, context=context)

            mock_ask.assert_awaited_once_with("how many leads do I have?")
            say.assert_awaited_once()
            assert "42 leads" in say.call_args.kwargs.get("text", say.call_args[1].get("text", ""))

    @pytest.mark.asyncio
    async def test_dm_handler_ignores_subtypes(self, monkeypatch):
        monkeypatch.setenv("EPI_API_KEY", "epi_test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        app_mock = MagicMock()
        captured_handlers: dict = {}

        def capture_event(event_type):
            def decorator(fn):
                captured_handlers[event_type] = fn
                return fn
            return decorator

        app_mock.event = capture_event

        from app.handlers import register_handlers
        register_handlers(app_mock)

        dm_handler = captured_handlers["message"]
        say = AsyncMock()

        # message_changed events should be ignored
        event = {
            "subtype": "message_changed",
            "text": "edited message",
            "channel_type": "im",
            "ts": "111",
            "team": "T01WORKSPACE",
        }
        await dm_handler(event=event, say=say, context={"team_id": "T01WORKSPACE"})
        say.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dm_handler_ignores_non_im_channels(self, monkeypatch):
        monkeypatch.setenv("EPI_API_KEY", "epi_test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        app_mock = MagicMock()
        captured_handlers: dict = {}

        def capture_event(event_type):
            def decorator(fn):
                captured_handlers[event_type] = fn
                return fn
            return decorator

        app_mock.event = capture_event

        from app.handlers import register_handlers
        register_handlers(app_mock)

        dm_handler = captured_handlers["message"]
        say = AsyncMock()

        event = {
            "text": "hello",
            "channel_type": "channel",
            "ts": "111",
            "team": "T01WORKSPACE",
        }
        await dm_handler(event=event, say=say, context={"team_id": "T01WORKSPACE"})
        say.assert_not_awaited()


# ------------------------------------------------------------------
# Data fetcher unit tests
# ------------------------------------------------------------------

class TestDataFetcher:
    @pytest.mark.asyncio
    async def test_get_leads_stats(self, monkeypatch):
        from app.data_fetcher import EPIBackendClient

        mock_response = {
            "total_leads": 100,
            "verified": 40,
            "likely_real": 30,
            "suspicious": 20,
            "junk": 10,
            "duplicates": 5,
            "attributed": 80,
            "unattributed": 20,
            "avg_quality_score": 72.5,
        }

        async def mock_get(self_inner, path, params=None):
            assert path == "/api/leads/stats"
            return mock_response

        monkeypatch.setattr(EPIBackendClient, "_get", mock_get)

        client = EPIBackendClient(base_url="http://localhost:8000", api_key="epi_test")
        result = await client.get_leads_stats()
        assert result["total_leads"] == 100
        assert result["verified"] == 40

    @pytest.mark.asyncio
    async def test_get_sites(self, monkeypatch):
        from app.data_fetcher import EPIBackendClient

        mock_sites = [
            {"id": "abc-123", "name": "My Site", "domain": "example.com"},
        ]

        async def mock_get(self_inner, path, params=None):
            assert path == "/api/sites"
            return mock_sites

        monkeypatch.setattr(EPIBackendClient, "_get", mock_get)

        client = EPIBackendClient(base_url="http://localhost:8000", api_key="epi_test")
        result = await client.get_sites()
        assert len(result) == 1
        assert result[0]["name"] == "My Site"

    @pytest.mark.asyncio
    async def test_get_comparison(self, monkeypatch):
        from app.data_fetcher import EPIBackendClient

        mock_data = [
            {
                "site_id": "abc-123",
                "platform": "google_ads",
                "report_date": "2025-01-15",
                "platform_conversions": 50,
                "platform_clicks": 500,
                "platform_spend": 1500.00,
                "epi_total_leads": 45,
                "epi_verified_leads": 30,
                "epi_junk_leads": 10,
                "discrepancy_pct": 10.0,
                "cost_per_verified_lead": 50.00,
            },
        ]

        async def mock_get(self_inner, path, params=None):
            assert path == "/api/comparison"
            return mock_data

        monkeypatch.setattr(EPIBackendClient, "_get", mock_get)

        client = EPIBackendClient(base_url="http://localhost:8000", api_key="epi_test")
        result = await client.get_comparison(platform="google_ads")
        assert len(result) == 1
        assert result[0]["platform"] == "google_ads"
