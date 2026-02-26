/**
 * fields.ts — Field identification heuristics.
 * Classifies form input fields as email, name, phone, etc. based on
 * the input's name, type, id, autocomplete, and placeholder attributes.
 */

export interface ClassifiedField {
  /** Original field name/id used as the dict key. */
  key: string;
  /** The semantic label we assigned. */
  label: string;
  /** The field's value. */
  value: string;
}

type FieldCategory = "email" | "first_name" | "last_name" | "full_name" | "phone" | "company" | "message" | "unknown";

/**
 * Pattern sets used for heuristic matching. Order matters — first match wins.
 */
const PATTERNS: Array<{ category: FieldCategory; re: RegExp }> = [
  { category: "email",      re: /email|e-mail|correo/i },
  { category: "phone",      re: /phone|tel|mobile|cell|fax|whatsapp/i },
  { category: "first_name", re: /first.?name|fname|given.?name|nombre/i },
  { category: "last_name",  re: /last.?name|lname|surname|family.?name|apellido/i },
  { category: "full_name",  re: /^name$|full.?name|your.?name|contact.?name/i },
  { category: "company",    re: /company|organization|business|empresa/i },
  { category: "message",    re: /message|comment|note|description|inquiry|msg/i },
];

/**
 * Build a single string from all identifying attributes for matching.
 */
function fingerprint(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement): string {
  return [
    el.getAttribute("name") ?? "",
    el.getAttribute("id") ?? "",
    el.getAttribute("type") ?? "",
    el.getAttribute("autocomplete") ?? "",
    el.getAttribute("placeholder") ?? "",
    el.getAttribute("aria-label") ?? "",
  ].join(" ");
}

/**
 * Classify a single form element.
 */
function classify(el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement): FieldCategory {
  // type="email" is an instant hit
  if (el instanceof HTMLInputElement && el.type === "email") return "email";
  if (el instanceof HTMLInputElement && el.type === "tel") return "phone";

  const fp = fingerprint(el);

  for (const { category, re } of PATTERNS) {
    if (re.test(fp)) return category;
  }

  return "unknown";
}

/**
 * Given a form element, extract all meaningful input values and classify them.
 * Returns a flat object mapping semantic labels (or raw names) to their values.
 * Hidden inputs, password fields, and submit/button types are excluded.
 */
export function extractFields(form: HTMLFormElement): Record<string, string> {
  const result: Record<string, string> = {};

  const elements = form.querySelectorAll<
    HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
  >("input, textarea, select");

  for (const el of elements) {
    // Skip inputs that shouldn't be captured.
    if (el instanceof HTMLInputElement) {
      const skipTypes = ["hidden", "password", "submit", "button", "image", "reset", "file"];
      if (skipTypes.includes(el.type)) continue;

      // Skip unchecked checkboxes / radio buttons.
      if ((el.type === "checkbox" || el.type === "radio") && !el.checked) continue;
    }

    // Skip the honeypot field that we injected.
    if (el.getAttribute("data-epi-hp") === "1") continue;

    const value = el.value.trim();
    if (!value) continue;

    const category = classify(el);

    // Use the category as key if recognized, otherwise fall back to name/id.
    const key =
      category !== "unknown"
        ? category
        : el.getAttribute("name") || el.getAttribute("id") || `field_${Math.random().toString(36).slice(2, 6)}`;

    result[key] = value;
  }

  return result;
}
