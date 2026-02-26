import pytest

from app.services.bot_detector import detect_bot
from app.services.lead_scorer import score_lead
from app.services.attribution import determine_attribution


def test_bot_detect_honeypot():
    is_bot, reasons = detect_bot(honeypot_value="filled", form_fill_time_ms=5000, user_agent="Mozilla/5.0")
    assert is_bot is True
    assert "honeypot_triggered" in reasons


def test_bot_detect_fast_fill():
    is_bot, reasons = detect_bot(honeypot_value=None, form_fill_time_ms=200, user_agent="Mozilla/5.0")
    assert is_bot is True
    assert any("too_fast" in r for r in reasons)


def test_bot_detect_bot_ua():
    is_bot, reasons = detect_bot(honeypot_value=None, form_fill_time_ms=5000, user_agent="Googlebot/2.1")
    assert is_bot is True


def test_bot_detect_clean():
    is_bot, reasons = detect_bot(honeypot_value=None, form_fill_time_ms=5000, user_agent="Mozilla/5.0")
    assert is_bot is False


def test_score_verified_lead():
    score, label = score_lead(
        email_valid="valid", phone_valid="mobile", is_bot=False,
        is_duplicate=False, honeypot_triggered=False,
        form_fill_time_ms=5000, has_gclid=True, has_fbclid=False,
    )
    assert score >= 75
    assert label == "verified"


def test_score_junk_lead():
    score, label = score_lead(
        email_valid="invalid", phone_valid="invalid", is_bot=True,
        is_duplicate=True, honeypot_triggered=True,
        form_fill_time_ms=100, has_gclid=False, has_fbclid=False,
    )
    assert score < 25
    assert label == "junk"


def test_attribution_definitive_gclid():
    tier = determine_attribution(gclid="abc123", fbclid=None, utm_source=None, utm_medium=None, referrer=None)
    assert tier == "definitive"


def test_attribution_definitive_fbclid():
    tier = determine_attribution(gclid=None, fbclid="fb123", utm_source=None, utm_medium=None, referrer=None)
    assert tier == "definitive"


def test_attribution_high_confidence():
    tier = determine_attribution(gclid=None, fbclid=None, utm_source="google", utm_medium="cpc", referrer=None)
    assert tier == "high_confidence"


def test_attribution_probable_utm():
    tier = determine_attribution(gclid=None, fbclid=None, utm_source="newsletter", utm_medium=None, referrer=None)
    assert tier == "probable"


def test_attribution_probable_referrer():
    tier = determine_attribution(gclid=None, fbclid=None, utm_source=None, utm_medium=None, referrer="https://www.google.com/search")
    assert tier == "probable"


def test_attribution_unattributed():
    tier = determine_attribution(gclid=None, fbclid=None, utm_source=None, utm_medium=None, referrer=None)
    assert tier == "unattributed"
