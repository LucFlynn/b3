/**
 * pixel.test.ts — Unit tests for the EPI pixel modules.
 * Uses vitest with jsdom environment.
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, vi } from "vitest";

// ---------------------------------------------------------------
// cookie.ts
// ---------------------------------------------------------------
describe("cookie module", () => {
  beforeEach(() => {
    // Clear cookies.
    document.cookie.split(";").forEach((c) => {
      const name = c.split("=")[0].trim();
      if (name) {
        document.cookie = `${name}=; max-age=0; path=/`;
      }
    });
    localStorage.clear();
  });

  it("getVisitorId returns a consistent UUID", async () => {
    const { getVisitorId } = await import("../src/cookie");
    const vid1 = getVisitorId();
    expect(vid1).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );

    // Second call should return the same visitor_id.
    const vid2 = getVisitorId();
    expect(vid2).toBe(vid1);
  });

  it("getSessionId returns a UUID and refreshes on each call", async () => {
    const { getSessionId } = await import("../src/cookie");
    const sid1 = getSessionId();
    expect(sid1).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
    );

    const sid2 = getSessionId();
    expect(sid2).toBe(sid1);
  });

  it("falls back to localStorage when cookies are unavailable", async () => {
    // Simulate cookie unavailability by overriding document.cookie getter.
    const original = Object.getOwnPropertyDescriptor(Document.prototype, "cookie");
    Object.defineProperty(document, "cookie", {
      get: () => "",
      set: () => {
        /* no-op */
      },
      configurable: true,
    });

    // Re-import to get fresh state.
    vi.resetModules();
    const { getVisitorId } = await import("../src/cookie");
    const vid = getVisitorId();
    expect(vid).toBeTruthy();
    expect(localStorage.getItem("_epi_vid")).toBeTruthy();

    // Restore.
    if (original) {
      Object.defineProperty(document, "cookie", original);
    } else {
      Object.defineProperty(Document.prototype, "cookie", original!);
    }
  });
});

// ---------------------------------------------------------------
// params.ts
// ---------------------------------------------------------------
describe("params module", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("captureParams extracts UTM parameters from the URL", async () => {
    // jsdom lets us set window.location via a workaround.
    Object.defineProperty(window, "location", {
      value: new URL(
        "https://example.com/?utm_source=google&utm_medium=cpc&gclid=abc123"
      ),
      writable: true,
    });

    const { captureParams } = await import("../src/params");
    const params = captureParams();

    expect(params.utm_source).toBe("google");
    expect(params.utm_medium).toBe("cpc");
    expect(params.gclid).toBe("abc123");
    expect(params.utm_campaign).toBeUndefined();
  });

  it("persists params across calls via sessionStorage", async () => {
    Object.defineProperty(window, "location", {
      value: new URL("https://example.com/?fbclid=fb_999"),
      writable: true,
    });

    vi.resetModules();
    const { captureParams, getParams } = await import("../src/params");
    captureParams();

    // Simulate a new page load without fbclid.
    Object.defineProperty(window, "location", {
      value: new URL("https://example.com/page2"),
      writable: true,
    });

    const stored = getParams();
    expect(stored.fbclid).toBe("fb_999");
  });
});

// ---------------------------------------------------------------
// fields.ts
// ---------------------------------------------------------------
describe("fields module", () => {
  it("extracts and classifies email, name, phone fields", async () => {
    const { extractFields } = await import("../src/fields");

    document.body.innerHTML = `
      <form id="test-form">
        <input type="email" name="email" value="test@example.com" />
        <input type="text" name="first_name" value="Jane" />
        <input type="text" name="last_name" value="Doe" />
        <input type="tel" name="phone" value="+1234567890" />
        <input type="text" name="company" value="Acme Inc" />
        <textarea name="message">Hello world</textarea>
        <input type="hidden" name="csrf" value="token123" />
        <input type="submit" value="Submit" />
      </form>
    `;

    const form = document.getElementById("test-form") as HTMLFormElement;
    const fields = extractFields(form);

    expect(fields.email).toBe("test@example.com");
    expect(fields.first_name).toBe("Jane");
    expect(fields.last_name).toBe("Doe");
    expect(fields.phone).toBe("+1234567890");
    expect(fields.company).toBe("Acme Inc");
    expect(fields.message).toBe("Hello world");
    // Hidden and submit inputs should be excluded.
    expect(fields.csrf).toBeUndefined();
  });

  it("skips the honeypot field", async () => {
    const { extractFields } = await import("../src/fields");

    document.body.innerHTML = `
      <form id="hp-form">
        <input type="email" name="email" value="test@example.com" />
        <input type="text" name="hp_field" data-epi-hp="1" value="bot-filled" />
      </form>
    `;

    const form = document.getElementById("hp-form") as HTMLFormElement;
    const fields = extractFields(form);

    expect(fields.email).toBe("test@example.com");
    expect(fields.hp_field).toBeUndefined();
  });
});

// ---------------------------------------------------------------
// honeypot.ts
// ---------------------------------------------------------------
describe("honeypot module", () => {
  it("injects a hidden field into a form", async () => {
    const { injectHoneypot, getHoneypotValue } = await import("../src/honeypot");

    document.body.innerHTML = `<form id="hp-test"><input type="text" name="name" /></form>`;
    const form = document.getElementById("hp-test") as HTMLFormElement;

    injectHoneypot(form);

    const hpInput = form.querySelector<HTMLInputElement>('[data-epi-hp="1"]');
    expect(hpInput).not.toBeNull();
    expect(hpInput!.name).toBe("_epi_hp_email");
    expect(hpInput!.tabIndex).toBe(-1);

    // Value should be empty for legitimate users.
    expect(getHoneypotValue(form)).toBe("");
  });

  it("does not inject twice", async () => {
    const { injectHoneypot } = await import("../src/honeypot");

    document.body.innerHTML = `<form id="hp-dup"><input type="text" name="name" /></form>`;
    const form = document.getElementById("hp-dup") as HTMLFormElement;

    injectHoneypot(form);
    injectHoneypot(form);

    const hpInputs = form.querySelectorAll('[data-epi-hp="1"]');
    expect(hpInputs.length).toBe(1);
  });

  it("getFormFillTime returns 0 when no interaction occurred", async () => {
    const { getFormFillTime } = await import("../src/honeypot");

    document.body.innerHTML = `<form id="hp-time"></form>`;
    const form = document.getElementById("hp-time") as HTMLFormElement;

    expect(getFormFillTime(form)).toBe(0);
  });
});

// ---------------------------------------------------------------
// beacon.ts
// ---------------------------------------------------------------
describe("beacon module", () => {
  it("sendEvent calls navigator.sendBeacon with correct payload", async () => {
    const mockSendBeacon = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, "sendBeacon", {
      value: mockSendBeacon,
      writable: true,
      configurable: true,
    });

    vi.resetModules();
    const { configure, sendEvent } = await import("../src/beacon");

    configure("https://api.example.com/api/event", "px_test123");

    sendEvent({ event_type: "pageview" });

    expect(mockSendBeacon).toHaveBeenCalledTimes(1);

    const [url, blob] = mockSendBeacon.mock.calls[0];
    expect(url).toBe("https://api.example.com/api/event");
    expect(blob).toBeInstanceOf(Blob);

    // Read and parse the blob (use FileReader for jsdom compat).
    const text = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsText(blob as Blob);
    });
    const payload = JSON.parse(text);

    expect(payload.pixel_id).toBe("px_test123");
    expect(payload.event_type).toBe("pageview");
    expect(payload.visitor_id).toBeTruthy();
    expect(payload.session_id).toBeTruthy();
    expect(payload.user_agent).toBeTruthy();
    expect(payload.timestamp).toBeGreaterThan(0);
  });

  it("falls back to fetch when sendBeacon is unavailable", async () => {
    Object.defineProperty(navigator, "sendBeacon", {
      value: undefined,
      writable: true,
      configurable: true,
    });

    const mockFetch = vi.fn().mockResolvedValue(new Response("ok"));
    global.fetch = mockFetch;

    vi.resetModules();
    const { configure, sendEvent } = await import("../src/beacon");

    configure("https://api.example.com/api/event", "px_fallback");
    sendEvent({ event_type: "pageview" });

    expect(mockFetch).toHaveBeenCalledTimes(1);

    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("https://api.example.com/api/event");
    expect(options.method).toBe("POST");
    expect(options.keepalive).toBe(true);

    const body = JSON.parse(options.body);
    expect(body.pixel_id).toBe("px_fallback");
  });
});

// ---------------------------------------------------------------
// api.ts
// ---------------------------------------------------------------
describe("api module", () => {
  it("epi('track', ...) sends a track event", async () => {
    const mockSendBeacon = vi.fn().mockReturnValue(true);
    Object.defineProperty(navigator, "sendBeacon", {
      value: mockSendBeacon,
      writable: true,
      configurable: true,
    });

    vi.resetModules();

    // Configure beacon first.
    const { configure } = await import("../src/beacon");
    configure("https://api.example.com/api/event", "px_api_test");

    const { epi } = await import("../src/api");
    epi("track", "Lead", { email: "test@example.com", name: "Jane" });

    expect(mockSendBeacon).toHaveBeenCalledTimes(1);

    const [, blob] = mockSendBeacon.mock.calls[0];
    const text = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsText(blob as Blob);
    });
    const payload = JSON.parse(text);

    expect(payload.event_type).toBe("track");
    expect(payload.form_data.email).toBe("test@example.com");
    expect(payload.form_data.name).toBe("Jane");
    expect(payload.extra.event_name).toBe("Lead");
  });

  it("ignores calls without a command or event name", async () => {
    vi.resetModules();
    const { epi } = await import("../src/api");

    // These should not throw.
    epi("", "Something");
    epi("track");
    epi("track", undefined);
  });
});
