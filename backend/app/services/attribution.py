from app.models.pageview import Pageview


def determine_attribution(
    gclid: str | None,
    fbclid: str | None,
    utm_source: str | None,
    utm_medium: str | None,
    referrer: str | None,
) -> str:
    """
    Attribution tiers:
    - definitive: direct click ID (gclid or fbclid)
    - high_confidence: UTM source + medium match known ad platforms
    - probable: UTM source present or referrer from known ad domain
    - unattributed: no attribution signal found
    """
    # Tier 1: Definitive — direct click IDs
    if gclid:
        return "definitive"
    if fbclid:
        return "definitive"

    # Tier 2: High confidence — UTM params match ad platforms
    ad_sources = {"google", "google_ads", "facebook", "fb", "meta", "instagram", "ig"}
    ad_mediums = {"cpc", "cpm", "paid", "ppc", "paid_social", "display"}
    if utm_source and utm_medium:
        if utm_source.lower() in ad_sources and utm_medium.lower() in ad_mediums:
            return "high_confidence"

    # Tier 3: Probable — some UTM or referrer signal
    if utm_source:
        return "probable"
    ad_domains = ["google.com", "facebook.com", "instagram.com", "meta.com"]
    if referrer:
        for domain in ad_domains:
            if domain in referrer.lower():
                return "probable"

    return "unattributed"
