def score_lead(
    email_valid: str | None,
    phone_valid: str | None,
    is_bot: bool,
    is_duplicate: bool,
    honeypot_triggered: bool,
    form_fill_time_ms: int | None,
    has_gclid: bool,
    has_fbclid: bool,
) -> tuple[int, str]:
    """Returns (score: 0-100, label: verified|likely_real|suspicious|junk)."""
    score = 50  # baseline

    # Bot detection is heavily penalizing
    if is_bot:
        score -= 40
    if honeypot_triggered:
        score -= 30

    # Duplicate
    if is_duplicate:
        score -= 20

    # Email validation
    if email_valid == "valid":
        score += 20
    elif email_valid == "catch_all":
        score += 5
    elif email_valid == "disposable":
        score -= 15
    elif email_valid == "invalid":
        score -= 25

    # Phone validation
    if phone_valid in ("valid", "mobile"):
        score += 15
    elif phone_valid == "landline":
        score += 5
    elif phone_valid == "voip":
        score -= 5
    elif phone_valid == "invalid":
        score -= 15

    # Attribution signals boost
    if has_gclid or has_fbclid:
        score += 10

    # Form timing
    if form_fill_time_ms and form_fill_time_ms > 3000:
        score += 5  # reasonable human timing

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

    return score, label
