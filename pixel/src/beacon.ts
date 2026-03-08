/**
 * beacon.ts — Sends event payloads to the backend.
 * Uses navigator.sendBeacon for reliability on page unload, with a fetch
 * POST fallback for environments where sendBeacon is unavailable.
 */

import { getVisitorId, getSessionId } from "./cookie";
import { getParams, type TrackedParams } from "./params";

/** Resolved once the pixel knows its endpoint. */
let endpointUrl = "";

/** The pixel_id extracted from the script tag data attribute. */
let pixelId = "";

/** Debug mode — logs all events and responses to console. */
let debugMode = false;

/**
 * Lightweight browser fingerprint — NOT meant for cross-site tracking.
 * Just enough entropy to correlate sessions on the same device.
 */
function fingerprint(): string {
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width + "x" + screen.height,
    screen.colorDepth,
    Intl.DateTimeFormat().resolvedOptions().timeZone,
  ];
  // Simple djb2 hash.
  let hash = 5381;
  const str = components.join("|");
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) & 0xffffffff;
  }
  return (hash >>> 0).toString(36);
}

/**
 * Configure the beacon module with the endpoint URL and pixel_id.
 */
export function configure(endpoint: string, id: string, debug: boolean = false): void {
  endpointUrl = endpoint;
  pixelId = id;
  debugMode = debug;
}

export interface EventData {
  event_type: string;
  form_id?: string;
  form_action?: string;
  form_data?: Record<string, string>;
  honeypot_value?: string;
  form_fill_time_ms?: number;
  extra?: Record<string, unknown>;
}

/**
 * Build a full EventPayload matching the backend schema.
 */
function buildPayload(data: EventData): Record<string, unknown> {
  const params: TrackedParams = getParams();

  return {
    pixel_id: pixelId,
    event_type: data.event_type,
    visitor_id: getVisitorId(),
    session_id: getSessionId(),
    page_url: window.location.href,
    referrer: document.referrer || null,
    user_agent: navigator.userAgent,
    fingerprint: fingerprint(),
    timestamp: Date.now(),

    // URL params
    utm_source: params.utm_source ?? null,
    utm_medium: params.utm_medium ?? null,
    utm_campaign: params.utm_campaign ?? null,
    utm_content: params.utm_content ?? null,
    utm_term: params.utm_term ?? null,
    gclid: params.gclid ?? null,
    fbclid: params.fbclid ?? null,

    // Form data
    form_id: data.form_id ?? null,
    form_action: data.form_action ?? null,
    form_data: data.form_data ?? null,

    // Bot detection
    honeypot_value: data.honeypot_value ?? null,
    form_fill_time_ms: data.form_fill_time_ms ?? null,

    // Extra
    extra: data.extra ?? null,
  };
}

/**
 * Send an event to the backend.
 * Prefers sendBeacon for fire-and-forget reliability, falls back to fetch.
 */
export function sendEvent(data: EventData): void {
  if (!endpointUrl || !pixelId) return;

  const payload = buildPayload(data);
  const json = JSON.stringify(payload);

  // Debug mode: use fetch so we can inspect the response.
  if (debugMode) {
    console.log("[EPI debug] sending:", data.event_type, payload);
    fetch(endpointUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json,
    })
      .then((r) => {
        if (r.ok) {
          console.log("[EPI debug]", data.event_type, "->", r.status, "OK");
        } else {
          r.text().then((t) =>
            console.error("[EPI debug]", data.event_type, "->", r.status, t)
          );
        }
      })
      .catch((err) => console.error("[EPI debug] network error:", err));
    return;
  }

  // Try sendBeacon first — works even during page unload.
  // Use text/plain to avoid CORS preflight (sendBeacon silently fails on preflight).
  // Backend parses JSON from body regardless of content-type.
  if (typeof navigator.sendBeacon === "function") {
    const blob = new Blob([json], { type: "text/plain" });
    const queued = navigator.sendBeacon(endpointUrl, blob);
    if (queued) return;
  }

  // Fallback: fetch with keepalive.
  try {
    fetch(endpointUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json,
      keepalive: true,
    }).catch(() => {
      // Silently ignore network errors — this is a tracking pixel.
    });
  } catch {
    // Ignore — tracking should never break the host page.
  }
}
