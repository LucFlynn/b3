/**
 * params.ts — Captures URL parameters (utm_*, gclid, fbclid) from the current
 * page URL and persists them in sessionStorage so they survive SPA navigations
 * and are available when forms are submitted later in the session.
 */

const STORAGE_KEY = "_epi_params";

/** The set of URL parameters we care about. */
const TRACKED_PARAMS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
  "gclid",
  "fbclid",
] as const;

export type TrackedParams = {
  [K in (typeof TRACKED_PARAMS)[number]]?: string;
};

/**
 * Read previously stored params from sessionStorage.
 */
function loadStored(): TrackedParams {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as TrackedParams;
  } catch {
    // sessionStorage unavailable — return empty.
  }
  return {};
}

/**
 * Persist params to sessionStorage.
 */
function persist(params: TrackedParams): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(params));
  } catch {
    // Silently ignore storage errors.
  }
}

/**
 * Parse tracked parameters from the current URL. New values overwrite
 * previously stored ones; keys not present in the URL keep their stored value.
 */
export function captureParams(): TrackedParams {
  const stored = loadStored();
  const url = new URL(window.location.href);

  let updated = false;

  for (const key of TRACKED_PARAMS) {
    const value = url.searchParams.get(key);
    if (value !== null) {
      stored[key] = value;
      updated = true;
    }
  }

  if (updated) {
    persist(stored);
  }

  return stored;
}

/**
 * Return the current set of tracked params (from sessionStorage).
 */
export function getParams(): TrackedParams {
  return loadStored();
}
