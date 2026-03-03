import logging
from datetime import datetime, timezone

import resend

from app.config import settings
from app.models.lead import Lead
from app.models.site import Site
from app.security import decrypt_pii

logger = logging.getLogger(__name__)


def _quality_color(label: str) -> str:
    return {
        "verified": "#22c55e",
        "likely_real": "#3b82f6",
        "suspicious": "#f59e0b",
        "junk": "#ef4444",
    }.get(label or "", "#6b7280")


async def send_lead_notification(lead: Lead, site: Site) -> None:
    if not settings.resend_api_key or not settings.notification_email:
        logger.debug("Email notifications not configured, skipping")
        return

    resend.api_key = settings.resend_api_key

    name = decrypt_pii(lead.name_encrypted) if lead.name_encrypted else "—"
    email = decrypt_pii(lead.email_encrypted) if lead.email_encrypted else "—"
    phone = decrypt_pii(lead.phone_encrypted) if lead.phone_encrypted else "—"
    color = _quality_color(lead.quality_label)
    ts = lead.created_at or datetime.now(timezone.utc)
    timestamp = ts.strftime("%Y-%m-%d %H:%M:%S UTC")

    source_parts = []
    if lead.utm_source:
        source_parts.append(f"{lead.utm_source}")
    if lead.utm_medium:
        source_parts.append(f"/ {lead.utm_medium}")
    if lead.utm_campaign:
        source_parts.append(f"/ {lead.utm_campaign}")
    if lead.gclid:
        source_parts.append("(gclid)")
    if lead.fbclid:
        source_parts.append("(fbclid)")
    attribution_source = " ".join(source_parts) if source_parts else "Direct / Unknown"

    subject = f"New Lead — {site.domain} — {lead.quality_label or 'unknown'} ({lead.quality_score})"

    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #111; color: #fff; padding: 20px; border-radius: 8px 8px 0 0;">
        <h2 style="margin: 0;">New Lead from {site.domain}</h2>
        <p style="margin: 4px 0 0; opacity: 0.7;">{timestamp}</p>
      </div>
      <div style="border: 1px solid #e5e7eb; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #6b7280; width: 140px;">Name</td>
            <td style="padding: 8px 0; font-weight: 600;">{name}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Email</td>
            <td style="padding: 8px 0;">{email}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Phone</td>
            <td style="padding: 8px 0;">{phone}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Quality</td>
            <td style="padding: 8px 0;">
              <span style="background: {color}; color: #fff; padding: 2px 10px; border-radius: 12px; font-size: 13px;">
                {lead.quality_label} ({lead.quality_score})
              </span>
            </td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Attribution</td>
            <td style="padding: 8px 0;">{lead.attribution_tier or 'unattributed'}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Source</td>
            <td style="padding: 8px 0;">{attribution_source}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Page URL</td>
            <td style="padding: 8px 0; word-break: break-all;">{lead.page_url or '—'}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Email Valid</td>
            <td style="padding: 8px 0;">{lead.email_valid or '—'}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #6b7280;">Phone Valid</td>
            <td style="padding: 8px 0;">{lead.phone_valid or '—'}</td>
          </tr>
        </table>
      </div>
      <p style="color: #9ca3af; font-size: 12px; text-align: center; margin-top: 16px;">
        EPI Lead Verification &mdash; {site.name}
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": settings.notification_from_email,
            "to": [settings.notification_email],
            "subject": subject,
            "html": html,
        })
        logger.info("Lead notification sent for lead %s", lead.id)
    except Exception:
        logger.exception("Failed to send lead notification email")
