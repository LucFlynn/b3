# B-Three Solutions — Landing Pages for Google Ads

## Client
**B-Three Solutions** — Pittsburgh-based custom software development firm.
Website: https://www.bthreesolutions.com/

## Positioning (use in all copy)
- "On Time | On Budget | On Shore"
- Fixed-fee pricing (not hourly — the quote is the price)
- One-year warranty on all deliverables
- 100% U.S.-based (on-shore) development team
- Pittsburgh, PA headquarters, serves clients nationwide
- Phone: (412) 555-1234 ← placeholder, replace with real number when provided

## Campaign Context
Google Ads campaign, $2,500/month budget split across 3 ad groups. Each landing page maps to one ad group. These are standalone landing pages — NO main site navigation. Goal is lead capture via form submission.

---

## 3 Landing Pages

### Page 1: `integration-services.html`
**Ad Group:** enterprise software integration, system integration consulting, ERP integration services
**Headline:** "Your Systems Don't Talk to Each Other. We Fix That."
**Target audience:** Ops/IT leaders with disconnected business systems (ERP, CRM, legacy, field service)

### Page 2: `legacy-modernization.html`
**Ad Group:** legacy software modernization, legacy application migration, legacy system upgrade, data consolidation software, data warehouse development services
**Headline:** "Your Software Is Holding Your Business Back. Let's Fix It — Without Starting Over."
**Target audience:** Companies stuck on old software, got a massive rebuild quote, need a smarter path

### Page 3: `operations-software.html`
**Ad Group:** work order management system, manufacturing quoting software, incident reporting system, mobile workforce management software, operational KPI dashboard
**Headline:** "Custom Operations Software — Built Exactly How Your Team Works"
**Target audience:** Operations teams that outgrew their off-the-shelf tools
**Special structure:** Hub page with 5 use-case cards so each keyword audience finds their section

---

## Design System

### Fonts
- **Headings:** Space Grotesk (Google Fonts) — weights 500, 600, 700
- **Body:** Inter (Google Fonts) — weights 400, 500, 600, 700, 800

### Colors
```css
--primary: #1B3A5C;       /* dark navy — headers, text, dark sections */
--primary-dark: #0F2440;  /* darker navy — hero gradients, topbar, footer */
--accent: #2E86DE;        /* blue — links, labels, card icons */
--orange: #F39C12;        /* orange — ALL CTA buttons, highlights */
--orange-hover: #E08A00;  /* orange hover state */
--light-bg: #F7F9FC;      /* light gray — alternating sections */
--card-bg: #FFFFFF;
--text: #1A1A2E;
--text-muted: #5A6377;
--border: #E2E8F0;
--success: #27AE60;       /* green — checkmarks in trust badges */
```

### Layout
- Max width: 1140px centered (container), 720px for content columns (cards, proof, hero text)
- **SINGLE COLUMN layout throughout** — no side-by-side tiles/cards. MecLabs principle: vertical flow draws the eye down the page toward CTA. Cards, proof blocks, use-case cards, hero, and CTA sections are all stacked vertically.
- Only exception: form field rows (name + company, email + phone) can be side-by-side on desktop
- Section padding: 80px vertical
- Card border-radius: 12px
- Button border-radius: 50px (pill shape)
- Alternating white / light-bg sections

### Responsive Breakpoints
- Desktop: > 900px (grid layouts, side-by-side hero)
- Tablet/Mobile: ≤ 900px (single column, hero visual hidden)
- Small mobile: ≤ 480px (tighter spacing)

### Icons
- Heroicons (inline SVG, stroke style, 1.5 stroke-width for cards, 2 for badges)
- No icon library loaded — all icons are inline `<svg>` tags

---

## Page Structure (shared across all 3)

1. **Top bar** — dark bg, phone left, 3 trust badges right
2. **Sticky header** — white, logo left, phone number right
3. **Hero** — dark gradient, headline + sub + CTA + badges left, visual diagram right
4. **Problem** — alt bg, 3 pain-point cards with red-accent icons
5. **Solution** — white bg, service cards (3 or 4 depending on page)
6. **How It Works** — 3 numbered steps with connecting line
7. **Social Proof** — case study cards + trust badge row
8. **FAQ** — 5 questions, simple expand style
9. **Bottom CTA** — dark gradient, left copy + right form card
10. **Footer** — dark, minimal
11. **Sticky mobile CTA** — fixed bottom bar, shows only on mobile

## Form Fields (every page)
- Full Name, Company, Email, Phone
- One qualifying dropdown or multi-select (varies per page)
- Optional textarea
- Orange submit button
- "No obligation" note below

---

## Case Studies Available (from their site)
Use these as proof points — match to the right page:

| Case Study | Best Page |
|---|---|
| Automated Reporting System — County Sheriff | Integration, Operations |
| Automated Reporting System — School Police | Integration, Operations |
| Extension of Software Life — Crime Mapping System | Legacy Modernization |
| Case Management — Internal Investigations | Integration |
| Sight On Scene — School Safety Real-Time Intelligence | Operations (incident) |
| Work Order Processing — Smartphone App | Operations (work orders) |
| Cloud-Based Software Package — Auto Inspections | Operations (inspection) |
| Data Warehousing services | Legacy Modernization |

## Content Gaps (no proof on site)
- Manufacturing quoting — no case study exists. Copy must stand alone.
- Mobile workforce management — thin proof. Lean on mobile app development experience.
- Business system integration — generic proof only.

---

## When Editing

- Keep all CSS in the `<style>` tag — no external stylesheets
- Keep all pages visually consistent (same colors, spacing, typography)
- CTA buttons are ALWAYS orange (`var(--orange)`)
- Never add main site navigation links — these are isolated landing pages
- Phone number appears in: top bar, sticky header, footer, CTA section
- The form `action="#"` is a placeholder — will be connected to their CRM/form handler later
- All pages must work on mobile — test at 375px width
- Page load target: under 3 seconds on mobile

## File Structure
```
/B3/
├── CLAUDE.md              ← this file
├── integration-services.html
├── legacy-modernization.html
└── operations-software.html
```

No build step. No dependencies. Just HTML files with Google Fonts.
