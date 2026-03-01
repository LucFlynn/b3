"""Anthropic Claude client with tool-use for querying EPI backend data.

Exposes a single ``ask()`` coroutine that accepts a user question, invokes
the relevant EPI backend tools via the Claude messages API, and returns
a plain-text answer suitable for posting in Slack.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from app.data_fetcher import EPIBackendClient

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 5

# ------------------------------------------------------------------
# Tool definitions (sent to Claude so it can decide which to call)
# ------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_leads_stats",
        "description": (
            "Retrieve lead quality statistics for the agency. "
            "Returns total leads, counts by quality label (verified, likely_real, "
            "suspicious, junk), duplicate count, attributed vs unattributed counts, "
            "and average quality score. Optionally filtered by site and date range."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "UUID of the site to filter by. Omit for all sites.",
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date/time in ISO-8601 format, e.g. 2025-01-01T00:00:00.",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date/time in ISO-8601 format, e.g. 2025-01-31T23:59:59.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_comparison",
        "description": (
            "Retrieve platform-vs-EPI attribution comparison data. "
            "Shows platform-reported conversions/clicks/spend alongside EPI-verified "
            "lead counts, discrepancy percentage, and cost per verified lead. "
            "Optionally filtered by site, platform (google_ads or meta_ads), and date range."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "UUID of the site to filter by. Omit for all sites.",
                },
                "platform": {
                    "type": "string",
                    "description": "Ad platform: 'google_ads' or 'meta_ads'. Omit for both.",
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date in ISO-8601 format, e.g. 2025-01-01.",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date in ISO-8601 format, e.g. 2025-01-31.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_recent_leads",
        "description": (
            "Retrieve the most recent leads with full details including "
            "name, email, phone, quality score, attribution, and all form fields. "
            "Use this when the user asks about specific leads, wants contact info, "
            "or asks 'who submitted a form' / 'what's the latest lead' / 'show me lead details'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "string",
                    "description": "UUID of the site to filter by. Omit for all sites.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of recent leads to return. Default 10, max 50.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_sites",
        "description": (
            "List all tracked sites (domains) for the agency. "
            "Returns site name, domain, pixel ID, connected ad account IDs, "
            "and pixel verification status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

SYSTEM_PROMPT = """\
You are the EPI (Enhanced Performance Intelligence) assistant — a concise \
Slack bot that answers questions about lead quality and attribution data.

Your agency's data is accessed through the tools provided. Call the appropriate \
tool(s) to fetch data, then compose a clear, scannable Slack message.

FORMATTING RULES — follow these strictly:

1. No preamble or filler. Jump straight to the data. Never start with \
   "Looking at...", "I can see...", "Let me check...", or similar.

2. When listing leads, use this exact format for each lead — one line per \
   lead, separated by a blank line:

   Name — Quality (score)
   Email | Phone | Source
   Program interest or key detail (if any)

   Example:
   Laura Cargill — :white_check_mark: Verified (75)
   lauracargill626@gmail.com | (586) 267-3496 | Meta · RCU UG
   Online Nursing, Summer 2026

   Shawn Gayle — :warning: Suspicious (45)
   wargod6684@gmail.com | — | Meta · General

3. After the lead list, add a one-line summary with counts, e.g.:
   5 new leads — 2 verified, 1 likely real, 1 suspicious, 1 test

4. Never use bold (*text*), italic (_text_), or other Slack markdown \
   formatting. Plain text only.

4. Omit fields that are empty or missing — don't show placeholders except \
   "—" for missing phone numbers.

5. Strip emojis and special characters from user-submitted form data.

6. For stats and comparisons, use compact tables or short bullet lists — \
   never walls of text.

7. Money as USD with two decimals. Percentages rounded to one decimal.

8. Never fabricate data. Only report what the tools return.

9. If a tool call errors, explain plainly and suggest what to try.

10. If you lack context to answer, ask for clarification.
"""


class ClaudeEPIClient:
    """Claude-powered natural-language interface to the EPI backend."""

    def __init__(self, anthropic_api_key: str, backend_client: EPIBackendClient) -> None:
        self._anthropic = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self._backend = backend_client

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    async def _execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Dispatch a tool call to the corresponding backend method."""
        logger.info("Executing tool %s with args %s", name, arguments)
        if name == "get_leads_stats":
            return await self._backend.get_leads_stats(
                site_id=arguments.get("site_id"),
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
            )
        if name == "get_comparison":
            return await self._backend.get_comparison(
                site_id=arguments.get("site_id"),
                platform=arguments.get("platform"),
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
            )
        if name == "get_recent_leads":
            return await self._backend.get_recent_leads(
                site_id=arguments.get("site_id"),
                limit=arguments.get("limit", 10),
            )
        if name == "get_sites":
            return await self._backend.get_sites()
        raise ValueError(f"Unknown tool: {name}")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def ask(self, user_message: str) -> str:
        """Send a user question through Claude with tool-use and return the final text answer."""
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message},
        ]

        for _round in range(MAX_TOOL_ROUNDS):
            response = await self._anthropic.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # If the model is done (no tool use), extract the final text.
            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            # If the model wants to use tools, execute them and feed results back.
            if response.stop_reason == "tool_use":
                # Append the assistant message that contains tool_use blocks.
                messages.append({"role": "assistant", "content": response.content})

                # Build tool result blocks for every tool_use in the response.
                tool_results: list[dict[str, Any]] = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    try:
                        result = await self._execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result, default=str),
                            }
                        )
                    except Exception as exc:
                        logger.exception("Tool %s failed", block.name)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps({"error": str(exc)}),
                                "is_error": True,
                            }
                        )

                messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason — return whatever text we have.
            return self._extract_text(response)

        # Exhausted tool rounds — return the last text we have.
        return "Sorry, I was unable to complete your request after several attempts. Please try rephrasing your question."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        """Pull plain text from a Claude response, joining multiple text blocks."""
        parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else "I was unable to generate a response."
