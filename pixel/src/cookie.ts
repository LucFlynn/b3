/**
 * cookie.ts — First-party cookie management for visitor_id and session_id.
 * Uses document.cookie with localStorage as a fallback when cookies are blocked.
 */

const VISITOR_KEY = "_epi_vid";
const SESSION_KEY = "_epi_sid";

/** Visitor cookie persists for 2 years. */
const VISITOR_MAX_AGE = 63072000; // 2 years in seconds

/** Session cookie persists for 30 minutes of inactivity. */
const SESSION_MAX_AGE = 1800; // 30 minutes in seconds

/**
 * Generate a v4-style UUID without crypto.randomUUID (broader compat).
 */
function uuid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback: manual v4 UUID
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Read a cookie value by name from document.cookie.
 */
function getCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)")
  );
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Set a first-party cookie with SameSite=Lax.
 */
function setCookie(name: string, value: string, maxAge: number): void {
  document.cookie =
    `${name}=${encodeURIComponent(value)}` +
    `; path=/` +
    `; max-age=${maxAge}` +
    `; SameSite=Lax`;
}

/**
 * Try localStorage as fallback storage.
 */
function lsGet(key: string): string | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { value: string; expires: number };
    if (Date.now() > parsed.expires) {
      localStorage.removeItem(key);
      return null;
    }
    return parsed.value;
  } catch {
    return null;
  }
}

function lsSet(key: string, value: string, maxAgeMs: number): void {
  try {
    localStorage.setItem(
      key,
      JSON.stringify({ value, expires: Date.now() + maxAgeMs })
    );
  } catch {
    // localStorage unavailable — silently ignore.
  }
}

/**
 * Read from cookie first, then fall back to localStorage.
 */
function read(key: string): string | null {
  return getCookie(key) ?? lsGet(key);
}

/**
 * Write to both cookie and localStorage.
 */
function write(key: string, value: string, maxAgeSec: number): void {
  setCookie(key, value, maxAgeSec);
  lsSet(key, value, maxAgeSec * 1000);
}

/**
 * Return the current visitor_id, creating one if it doesn't exist.
 */
export function getVisitorId(): string {
  let vid = read(VISITOR_KEY);
  if (!vid) {
    vid = uuid();
    write(VISITOR_KEY, vid, VISITOR_MAX_AGE);
  } else {
    // Refresh the expiry on every page load.
    write(VISITOR_KEY, vid, VISITOR_MAX_AGE);
  }
  return vid;
}

/**
 * Return the current session_id, creating one if it doesn't exist.
 * Refreshes the session expiry on every call.
 */
export function getSessionId(): string {
  let sid = read(SESSION_KEY);
  if (!sid) {
    sid = uuid();
  }
  // Always refresh session TTL.
  write(SESSION_KEY, sid, SESSION_MAX_AGE);
  return sid;
}
