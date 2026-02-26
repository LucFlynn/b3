/**
 * honeypot.ts — Injects a hidden honeypot field into detected forms and tracks
 * the time between form first-interaction and submit to detect bots.
 *
 * A real human will never fill in the hidden honeypot field and will take at
 * least a few seconds to fill in a form. Bots typically fill everything
 * instantly, including invisible fields.
 */

/** CSS that makes the honeypot visually invisible but still present in the DOM. */
const HP_STYLE =
  "position:absolute;left:-9999px;top:-9999px;width:0;height:0;overflow:hidden;opacity:0;pointer-events:none;tab-index:-1";

const HP_FIELD_NAME = "_epi_hp_email";

/** WeakMap to store the timestamp of first interaction per form. */
const interactionTimestamps = new WeakMap<HTMLFormElement, number>();

/**
 * Record the first interaction time on a form.
 */
function onFirstInteraction(form: HTMLFormElement): void {
  if (!interactionTimestamps.has(form)) {
    interactionTimestamps.set(form, Date.now());
  }
}

/**
 * Inject a honeypot field into a form element.
 * The field is visually hidden and uses an enticing name ("email") to lure bots.
 */
export function injectHoneypot(form: HTMLFormElement): void {
  // Don't inject twice.
  if (form.querySelector(`[data-epi-hp="1"]`)) return;

  const wrapper = document.createElement("div");
  wrapper.setAttribute("style", HP_STYLE);
  wrapper.setAttribute("aria-hidden", "true");

  const input = document.createElement("input");
  input.type = "text";
  input.name = HP_FIELD_NAME;
  input.setAttribute("tabindex", "-1");
  input.setAttribute("autocomplete", "off");
  input.setAttribute("data-epi-hp", "1");

  wrapper.appendChild(input);
  form.appendChild(wrapper);

  // Track first interaction (focus, keydown, click inside the form).
  const handler = () => onFirstInteraction(form);
  form.addEventListener("focusin", handler, { once: true, passive: true });
  form.addEventListener("keydown", handler, { once: true, passive: true });
  form.addEventListener("click", handler, { once: true, passive: true });
  // Also set timestamp on touch devices.
  form.addEventListener("touchstart", handler, { once: true, passive: true });
}

/**
 * Read the honeypot field value from a form.
 * Returns the value (empty string for real users, non-empty for bots).
 */
export function getHoneypotValue(form: HTMLFormElement): string {
  const input = form.querySelector<HTMLInputElement>(`[data-epi-hp="1"]`);
  return input ? input.value : "";
}

/**
 * Return the time in milliseconds between the user's first interaction with
 * the form and the current moment (i.e., when submit fires).
 * Returns 0 if no interaction was recorded (possible bot signal).
 */
export function getFormFillTime(form: HTMLFormElement): number {
  const start = interactionTimestamps.get(form);
  if (!start) return 0;
  return Date.now() - start;
}
