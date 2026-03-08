def score_lead(
    email_valid: str | None,
    phone_valid: str | None,
    is_bot: bool,
    is_duplicate: bool,
    honeypot_triggered: bool,
    form_fill_time_ms: int | None,
    has_gclid: bool,
    has_fbclid: bool,
    is_vpn_or_proxy: bool = False,
    is_datacenter: bool = False,
) -> tuple[int, str, list[dict]]:
    """Returns (score: 0-100, label, signals_fired)."""
    score = 50  # baseline
    signals = []

    def _signal(name: str, points: int, detail: str = ""):
        nonlocal score
        score += points
        signals.append({"signal": name, "points": points, "detail": detail})

    # Bot detection is heavily penalizing
    if is_bot:
        _signal("bot_detected", -40, "Automated submission detected")
    if honeypot_triggered:
        _signal("honeypot_triggered", -30, "Hidden field was filled")

    # Duplicate
    if is_duplicate:
        _signal("duplicate", -20, "Same contact submitted within 24h")

    # Email validation
    if email_valid == "valid":
        _signal("valid_email", 20, "Deliverable, not disposable")
    elif email_valid == "catch_all":
        _signal("catch_all_email", 5, "Catch-all domain, can't verify individual address")
    elif email_valid == "disposable":
        _signal("disposable_email", -15, "Disposable/temporary email provider")
    elif email_valid == "invalid":
        _signal("invalid_email", -25, "Email address is undeliverable")

    # Phone validation
    if phone_valid in ("valid", "mobile"):
        _signal("valid_phone", 15, f"Valid {phone_valid} number")
    elif phone_valid == "landline":
        _signal("landline_phone", 5, "Valid landline number")
    elif phone_valid == "voip":
        _signal("voip_phone", -5, "VOIP number (Google Voice, etc.)")
    elif phone_valid == "invalid":
        _signal("invalid_phone", -15, "Phone number is invalid")

    # IP intelligence
    if is_datacenter:
        _signal("datacenter_ip", -25, "Submitted from a datacenter/hosting IP")
    elif is_vpn_or_proxy:
        _signal("vpn_proxy", -10, "Submitted through VPN or proxy")

    # Attribution signals boost
    if has_gclid:
        _signal("gclid_present", 10, "Google Ads click ID detected")
    elif has_fbclid:
        _signal("fbclid_present", 10, "Meta Ads click ID detected")

    # Form timing
    if form_fill_time_ms and form_fill_time_ms > 3000:
        _signal("human_timing", 5, f"Form filled in {form_fill_time_ms / 1000:.1f}s")

    # Clamp
    score = max(0, min(100, score))

    # Label
    if score >= 75:
        label = "verified"
    elif score >= 50:
        label = "likely_real"
    elif score >= 25:
        label = "suspicious"
    else:
        label = "junk"

    return score, label, signals
