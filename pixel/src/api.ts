/**
 * api.ts — Public API exposed as window.epi().
 *
 * Usage:
 *   epi('track', 'Lead', { email: 'user@example.com', name: 'Jane' })
 *   epi('track', 'Signup', { plan: 'pro' })
 */

import { sendEvent, type EventData } from "./beacon";

type ApiCommand = "track";

/**
 * Process a single API call.
 */
function handleCommand(
  command: ApiCommand,
  eventName: string,
  data?: Record<string, unknown>
): void {
  switch (command) {
    case "track": {
      const formData: Record<string, string> = {};
      const extra: Record<string, unknown> = {};

      if (data) {
        for (const [key, val] of Object.entries(data)) {
          // Known form fields go into form_data, everything else into extra.
          if (typeof val === "string") {
            formData[key] = val;
          } else {
            extra[key] = val;
          }
        }
      }

      const eventData: EventData = {
        event_type: "track",
        form_data: Object.keys(formData).length > 0 ? formData : undefined,
        extra: Object.keys(extra).length > 0 ? { ...extra, event_name: eventName } : { event_name: eventName },
      };

      sendEvent(eventData);
      break;
    }
    default:
      // Unknown command — silently ignore.
      break;
  }
}

/**
 * The public epi() function. Can be called directly or used to flush
 * any queued calls that arrived before the script loaded.
 */
export function epi(
  command: string,
  eventName?: string,
  data?: Record<string, unknown>
): void {
  if (!command || !eventName) return;
  handleCommand(command as ApiCommand, eventName, data);
}

/**
 * Process any calls that were queued before the pixel script loaded.
 * Sites can push calls into window.epi.q = [] before the script tag.
 */
export function flushQueue(): void {
  const win = window as unknown as {
    epi?: {
      q?: Array<[string, string?, Record<string, unknown>?]>;
    };
  };

  const queue = win.epi?.q;
  if (Array.isArray(queue)) {
    for (const args of queue) {
      epi(args[0], args[1], args[2]);
    }
    // Clear the queue.
    queue.length = 0;
  }
}
