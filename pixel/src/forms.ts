/**
 * forms.ts — Three-tier form detection:
 *   1. Native HTML form submit events
 *   2. AJAX/fetch interception (XMLHttpRequest.send & window.fetch patches)
 *   3. MutationObserver for dynamically added forms
 */

import { extractFields } from "./fields";
import { injectHoneypot, getHoneypotValue, getFormFillTime } from "./honeypot";
import { sendEvent } from "./beacon";

/** Set of forms we've already attached listeners to (avoid duplicates). */
const trackedForms = new WeakSet<HTMLFormElement>();

/**
 * Handle a form submission: extract fields, honeypot, timing, then beacon.
 */
function handleFormSubmit(form: HTMLFormElement): void {
  const fields = extractFields(form);

  // Don't send events for forms with no meaningful data.
  if (Object.keys(fields).length === 0) return;

  const honeypotValue = getHoneypotValue(form);
  const fillTime = getFormFillTime(form);

  sendEvent({
    event_type: "form_submit",
    form_id: form.id || form.getAttribute("name") || undefined,
    form_action: form.action || undefined,
    form_data: fields,
    honeypot_value: honeypotValue,
    form_fill_time_ms: fillTime,
  });
}

/**
 * Attach submit listener to a single form.
 */
function trackForm(form: HTMLFormElement): void {
  if (trackedForms.has(form)) return;
  trackedForms.add(form);

  // Inject honeypot.
  injectHoneypot(form);

  // Tier 1: native submit event.
  form.addEventListener(
    "submit",
    () => {
      handleFormSubmit(form);
    },
    { passive: true }
  );
}

/**
 * Scan the document for all current forms and attach listeners.
 */
function scanExistingForms(): void {
  const forms = document.querySelectorAll<HTMLFormElement>("form");
  forms.forEach(trackForm);
}

// -------------------------------------------------------------------
// Tier 2: AJAX / Fetch interception
// -------------------------------------------------------------------

/**
 * Patch XMLHttpRequest.send to detect AJAX form posts.
 * We look for POST requests with body content that looks like form data.
 */
function patchXHR(): void {
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;

  const xhrMethods = new WeakMap<XMLHttpRequest, string>();
  const xhrUrls = new WeakMap<XMLHttpRequest, string>();

  XMLHttpRequest.prototype.open = function (
    method: string,
    url: string | URL,
    ...rest: unknown[]
  ) {
    xhrMethods.set(this, method.toUpperCase());
    xhrUrls.set(this, typeof url === "string" ? url : url.toString());
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (origOpen as any).call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function (body?: Document | XMLHttpRequestBodyInit | null) {
    const method = xhrMethods.get(this);
    const url = xhrUrls.get(this);

    if (method === "POST" && body && typeof body === "string") {
      try {
        const parsed = JSON.parse(body);
        if (typeof parsed === "object" && parsed !== null) {
          maybeBeaconAjaxForm(url, parsed as Record<string, unknown>);
        }
      } catch {
        // Not JSON — might be URL-encoded form data.
        if (body.includes("=")) {
          const params = new URLSearchParams(body);
          const obj: Record<string, string> = {};
          params.forEach((v, k) => {
            obj[k] = v;
          });
          if (Object.keys(obj).length > 0) {
            maybeBeaconAjaxForm(url, obj);
          }
        }
      }
    }

    return origSend.call(this, body);
  };
}

/**
 * Patch window.fetch to detect fetch-based form submissions.
 */
function patchFetch(): void {
  const origFetch = window.fetch;

  window.fetch = function (input: RequestInfo | URL, init?: RequestInit) {
    if (init?.method?.toUpperCase() === "POST" && init.body) {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      const body = init.body;

      if (typeof body === "string") {
        try {
          const parsed = JSON.parse(body);
          if (typeof parsed === "object" && parsed !== null) {
            maybeBeaconAjaxForm(url, parsed as Record<string, unknown>);
          }
        } catch {
          // URL-encoded
          if (body.includes("=")) {
            const params = new URLSearchParams(body);
            const obj: Record<string, string> = {};
            params.forEach((v, k) => {
              obj[k] = v;
            });
            if (Object.keys(obj).length > 0) {
              maybeBeaconAjaxForm(url, obj);
            }
          }
        }
      }
    }

    return origFetch.call(this, input, init);
  };
}

/**
 * Determine whether an AJAX POST body looks like form data with recognisable
 * contact fields (email, name, phone). If so, send a form_submit event.
 */
function maybeBeaconAjaxForm(
  url: string | undefined,
  data: Record<string, unknown>
): void {
  // Simple heuristic: does the payload contain an email-like value?
  const values = Object.values(data);
  const hasEmail = values.some(
    (v) => typeof v === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
  );

  if (!hasEmail) return;

  // Flatten everything to strings for form_data.
  const formData: Record<string, string> = {};
  for (const [key, val] of Object.entries(data)) {
    formData[key] = typeof val === "string" ? val : JSON.stringify(val);
  }

  sendEvent({
    event_type: "form_submit",
    form_action: url || undefined,
    form_data: formData,
    // No honeypot or timing for intercepted AJAX — we don't control the form.
    honeypot_value: undefined,
    form_fill_time_ms: undefined,
  });
}

// -------------------------------------------------------------------
// Tier 3: MutationObserver for dynamically added forms
// -------------------------------------------------------------------

function observeDynamicForms(): void {
  if (typeof MutationObserver === "undefined") return;

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (!(node instanceof HTMLElement)) continue;

        // If the added node IS a form.
        if (node.tagName === "FORM") {
          trackForm(node as HTMLFormElement);
        }

        // If the added node CONTAINS forms.
        const nestedForms = node.querySelectorAll<HTMLFormElement>("form");
        nestedForms.forEach(trackForm);
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

// -------------------------------------------------------------------
// Public init
// -------------------------------------------------------------------

/**
 * Initialize all three tiers of form detection.
 */
export function initForms(): void {
  // Tier 1: existing forms.
  scanExistingForms();

  // Tier 2: AJAX interception.
  patchXHR();
  patchFetch();

  // Tier 3: dynamic forms.
  observeDynamicForms();
}
