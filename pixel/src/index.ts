/**
 * index.ts — EPI Pixel entry point.
 *
 * Auto-initializes by reading the pixel_id from the script tag's
 * data-pixel-id attribute, then sets up cookie management, URL param
 * capture, form detection, and exposes the window.epi() public API.
 *
 * Usage in HTML:
 *   <script src="https://cdn.example.com/epi.min.js" data-pixel-id="px_abc123"></script>
 *
 * Manual event tracking:
 *   window.epi('track', 'Lead', { email: 'user@example.com' })
 */

import { getVisitorId, getSessionId } from "./cookie";
import { captureParams } from "./params";
import { configure, sendEvent } from "./beacon";
import { initForms } from "./forms";
import { epi as epiApi, flushQueue } from "./api";

/**
 * Discover the pixel_id from the <script> tag's data-pixel-id attribute.
 * Falls back to searching all script elements if document.currentScript is null.
 */
function discoverPixelId(): string | null {
  // Preferred: document.currentScript (set during synchronous execution).
  const current = document.currentScript as HTMLScriptElement | null;
  if (current) {
    const id = current.getAttribute("data-pixel-id");
    if (id) return id;
  }

  // Fallback: search all script tags for one with data-pixel-id.
  const scripts = document.querySelectorAll<HTMLScriptElement>("script[data-pixel-id]");
  if (scripts.length > 0) {
    return scripts[scripts.length - 1].getAttribute("data-pixel-id");
  }

  return null;
}

/**
 * Derive the API endpoint from the script's src attribute.
 * If the script is loaded from https://cdn.example.com/epi.min.js,
 * the endpoint becomes https://cdn.example.com/api/event.
 * Falls back to a relative /api/event path.
 */
function discoverEndpoint(): string {
  const current = document.currentScript as HTMLScriptElement | null;
  if (current?.src) {
    try {
      const url = new URL(current.src);
      return `${url.origin}/api/event`;
    } catch {
      // Invalid URL — fall through.
    }
  }

  // Check for explicit data-endpoint attribute.
  const scripts = document.querySelectorAll<HTMLScriptElement>("script[data-pixel-id]");
  for (const script of scripts) {
    const endpoint = script.getAttribute("data-endpoint");
    if (endpoint) return endpoint;

    if (script.src) {
      try {
        const url = new URL(script.src);
        return `${url.origin}/api/event`;
      } catch {
        // Invalid URL — fall through.
      }
    }
  }

  // Absolute fallback: relative path.
  return "/api/event";
}

/**
 * Main initialization routine. Runs once on script load.
 */
function isDebugMode(): boolean {
  // Enabled by data-debug attribute on script tag, or ?epi_debug=1 in URL.
  const scripts = document.querySelectorAll<HTMLScriptElement>("script[data-pixel-id]");
  for (const s of scripts) {
    if (s.hasAttribute("data-debug")) return true;
  }
  try {
    return new URLSearchParams(window.location.search).has("epi_debug");
  } catch {
    return false;
  }
}

function init(): void {
  const pixelId = discoverPixelId();
  if (!pixelId) {
    if (typeof console !== "undefined") {
      console.warn("[EPI] No data-pixel-id found on script tag. Pixel not initialized.");
    }
    return;
  }

  const endpoint = discoverEndpoint();
  const debug = isDebugMode();

  // 1. Configure the beacon module.
  configure(endpoint, pixelId, debug);

  if (debug) {
    console.log("[EPI debug] pixel_id:", pixelId, "endpoint:", endpoint);
  }

  // 2. Generate or restore visitor/session identifiers.
  getVisitorId();
  getSessionId();

  // 3. Capture URL params (utm_*, gclid, fbclid).
  captureParams();

  // 4. Send initial pageview event.
  sendEvent({ event_type: "pageview" });

  // 5. Initialize form detection (all three tiers).
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initForms());
  } else {
    initForms();
  }

  // 6. Expose the public API on window.epi and flush any queued calls.
  const win = window as unknown as Record<string, unknown>;
  win.epi = epiApi;
  flushQueue();
}

// -------------------------------------------------------------------
// Auto-initialize
// -------------------------------------------------------------------
try {
  init();
} catch (err) {
  // The pixel must never break the host page.
  if (typeof console !== "undefined") {
    console.error("[EPI] Initialization error:", err);
  }
}

// Re-export the public API for the IIFE `EPI` global.
export { epiApi as epi };
