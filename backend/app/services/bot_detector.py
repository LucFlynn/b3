import re

BOT_UA_PATTERNS = [
    r"bot", r"crawl", r"spider", r"scrape", r"headless",
    r"phantom", r"selenium", r"puppeteer", r"playwright",
]

# Minimum time in ms for a human to fill a form
MIN_HUMAN_FILL_TIME_MS = 800


def detect_bot(
    honeypot_value: str | None,
    form_fill_time_ms: int | None,
    user_agent: str | None,
) -> tuple[bool, list[str]]:
    """Returns (is_bot, reasons)."""
    reasons = []

    # Honeypot check
    if honeypot_value:
        reasons.append("honeypot_triggered")

    # Timing check
    if form_fill_time_ms is not None and form_fill_time_ms < MIN_HUMAN_FILL_TIME_MS:
        reasons.append(f"form_filled_too_fast:{form_fill_time_ms}ms")

    # User agent check
    if user_agent:
        ua_lower = user_agent.lower()
        for pattern in BOT_UA_PATTERNS:
            if re.search(pattern, ua_lower):
                reasons.append(f"bot_user_agent:{pattern}")
                break

    return len(reasons) > 0, reasons
