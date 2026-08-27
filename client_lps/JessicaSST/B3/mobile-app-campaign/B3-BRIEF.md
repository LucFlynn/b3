# B3 Solutions — Landing Page Project Brief

Context file for building and iterating on B-Three Solutions landing pages.
Read this first. Pair it with `LANDING-PAGE-RESEARCH.md` for the framework rules.

Agency: Electro Raven (Luc Flynn). Client: B-Three Solutions, Pittsburgh PA.
Branding rule: Electro Raven or unbranded. Never Onya, Highland Creative, Kobami, or Digital Treehouse.

**Current scope:** these HTML files are review prototypes, not production pages. Another party will
convert the approved direction into WordPress. Do not spend project time on form submission plumbing,
spam protection, hosting architecture, compiled assets, or other production implementation. Google Ads
work is being completed separately; the prototypes still need explicit message match to the campaign's
mobile-app-development keywords.

---

## The client

B-Three Solutions, Inc. — Pittsburgh software development firm. Custom web, mobile, and back-office
software. Also does project outsourcing and staff augmentation for other firms.

- 555 Davidson Road, Suite 4, Pittsburgh, PA 15239
- Phone on the LP: (412) 912-4705 (main office line is 412-712-1000)
- Main site: bthreesolutions.com (Wix)
- Current LP: software.bthreesolutions.com/b-three-mobile-app-development/ (WordPress + Elementor)
- Sibling company: B-Three Software (product: Sight On Scene, school/business security)

---

## Current performance — Google Ads, Jul 27 to Aug 25 2026

One campaign: `B3 | Search | Mobile App Dev | SST Exact`. $80/day, Maximize Clicks.

| Metric | Value |
|---|---|
| Spend | $1,794.80 |
| Clicks | 123 |
| Impressions | 3,878 |
| CTR | 3.17% |
| Avg CPC | $14.59 |
| Conversions | 1 |
| Conv. rate | **0.81%** |
| Cost per conversion | **$1,794.80** |
| Search impression share | 17.36% |
| Lost IS (rank) | 47.51% |
| Lost IS (budget) | 35.13% |

Benchmarks: Google Ads median conv. rate is 2.35% (WordStream/LocaliQ). Purpose-built landing page
median is 6.6% (Unbounce Q4 2024). B3 sits at roughly a third of the weaker one.

**Note on the campaign export:** the CSV segments by conversion action, which produces rows showing
0 impressions. The real numbers are on the `Total: Campaign` row. There is only one campaign.

### Quality Score — this is the core diagnosis

| Keyword | QS | Ad relevance | Landing page exp. |
|---|---|---|---|
| hire mobile app developers | 3 | Above average | **Below average** |
| custom mobile app development | 3 | Above average | **Below average** |
| enterprise mobile app development | 3 | Above average | **Below average** |
| mobile development services | 2 | Average | **Below average** |

Ad relevance is fine everywhere. Landing page experience is below average everywhere. That's Google
saying the page doesn't deliver what the ad promised. It's also why 47.51% of impression share is lost
to rank — QS is a direct input. Fixing the page lowers CPC and raises impression share on the same budget.

`[mobile development services]` is flagged **Limited: low quality**.

### Wasted spend in search terms (~31% of identified terms)

- **Spotify API developers — ~$179.** "create app spotify developer", "spotify for developers",
  "spotify developer dashboard create app", "spotify app creator", "create a spotify app". People
  registering an app in the Spotify dashboard. Zero commercial intent. Negatives needed immediately.
- **DIY / how-to — ~$75.** "how to make an app for your business", "how to create an app for business",
  "how to make a custom app". Want a tutorial, not a vendor.
- **Freelancer shoppers — ~$133.** "app developer for hire", "who can create an app for me" ($39 alone),
  "get an app built", "we build your app", "app creators for hire". Someone with an idea and a few
  thousand dollars.

Another $535 sits unattributed in "Other search terms," likely more of the same.

### The ad is recruiting the wrong buyer

One RSA, 11 of 15 headlines used, Ad strength Average.

**Remove:**
- `From Idea to App Store` — App Store signals consumer app. This single headline is the biggest driver
  of the freelancer and app-idea traffic. Contradicts everything else in the account.
- `Get an iOS, Android Devices` — broken grammar, currently live.
- `{Keyword:Near You}` — keyword insertion defaulting to "Near You," reads like a local trade business.

**Keep and build on:**
- `100% On-Shore Dev Team`
- `Fixed-Fee No Surprise Dev Work`
- `On Time & On Budget`
- `Trusted by Govt Agencies`

Those four are the positioning. They were in the ad and nowhere on the page.

---

## Competitive positioning

**DreamzTech** (dreamztech.com) — sells **scale and speed**. 450+ engineers, AI-led development,
2-3x faster, "US project leadership" layered over offshore delivery. Publishes price tiers
($25-60K / $60-150K / $150K+). Heavy award and logo stack: DHL, Nestlé, AB InBev, Avnet, Inc 5000,
Forbes, Clutch, 200+ reviews. Runs a comparison table that attacks US agencies as small and expensive.

**Bluelight** (bluelight.co) — sells **cheap and close**. Nearshore LATAM, claims 60% cost savings vs
US hires, timezone-aligned, radical vetting transparency (watch the coding challenges), dedicated
account manager, SOC 2.

Both sell **engineering capacity** — hours, headcount, rates. In both models the buyer still carries
the risk if the project goes sideways.

**The whitespace: nobody sells certainty.** The real fear for a mid-market ops or IT leader isn't the
hourly rate — it's the project that runs 18 months, eats triple the budget, and ships something nobody
uses. B3 already owns the three things that kill that fear and was treating them as feature bullets.

---

## The positioning

> **B-Three builds the software police departments file reports on. You get a fixed price and a fixed
> date in writing before a dollar moves, and a one-year warranty when it ships.**

### 3S breakdown

- **Specific person:** Operations and IT leaders at mid-market US companies and public agencies who
  cannot afford a software project to go sideways — either because they've been burned, or because
  they're the one who has to defend the number.
- **Specific problem:** The money pit. Projects that blow the budget and the date and never ship.
  Hourly billing means every delay is revenue for the vendor and cost for the client.
- **Specific way:** Fixed price + fixed delivery date + one-year warranty, all in writing before
  development starts. 30 engineers, all in Pittsburgh. Proven on public-safety systems where failure
  wasn't an option.

### Why it holds up against both competitors

- DreamzTech's 450 engineers and staff augmentation = you're renting capacity and still own the outcome.
- Bluelight's 60% savings = cheaper hours on a project that might still never ship.
- B3's smallness is the *reason* the offer is credible. A body shop selling capacity by the hour
  structurally cannot commit to a fixed scope and stand behind it for a year.
- **90% staff retention** answers a fear neither competitor can touch: will the team that starts my
  project still be here at the end? Offshore and staff-aug models churn.

---

## Proof inventory

Everything below is already public on B-Three's own site or LinkedIn. None of it was on the landing page.

### Named clients (published on their Success Stories page)
- **City of Pittsburgh** — Automated Police Reporting System (APRS)
- **Pittsburgh Bureau of Police** — MapStats crime plotting system
- **City of Pittsburgh Office of Municipal Investigations**
- **County Sheriff's Department** (large metro county, unnamed in their copy)
- **Major metropolitan school district** — adopted after seeing the Pittsburgh APRS demo
- Insurance agency (SharePoint image repository), engineering firm, other software firms (white-label)

### Numbers (from their LinkedIn / company profile)
- 30+ IT professionals
- 100+ clients
- In business over a decade
- **90% employee retention over the past decade**
- 100% of software developed in Pittsburgh, all personnel Pittsburgh-based

### Commitments they already make
- Fixed budget and timeline on every project
- One-year warranty against all defects
- "We solve business problems first. We build technology second."

### NEEDS CLIENT CONFIRMATION before launch
1. **Public-safety references still OK to name?** Some engagements are old. The copy uses City of
   Pittsburgh, Bureau of Police, Sheriff's Dept, and school district by name.
2. **Founding year.** The drafts use "since 2010" / "15+ years," inferred from "in business over a decade."
   Get the real year.
3. **Retention and headcount still current?** The 90% / 30+ figures come from their LinkedIn description.

### Confirmed NOT available
- Cannot name a government client as a *government contract* reference (but the case studies above are
  already public, which is different — flag this distinction to the client)
- Will not publish a delivery window — handled by promising "your date in writing," not a generic number
- Will not publish a price range — handled by removing the budget field from the form entirely

---

## The two pages

Same offer, same proof, two structures. Message match is constant so the test isolates structure.

### `lp-a-direct.html` — short, direct response
Near-black background, yellow accent, heavy Archivo type. Everything above the fold: claim, five-item
offer stack, proof block, and form side by side. Form sticks to viewport on desktop. No scrolling to
find the ask.

Headline: *"How to get your mobile app built — without a moving budget or a moving deadline."*

Leads with the offer. Best fit for higher-intent traffic and for anyone who already knows they need a vendor.

### `lp-b-sequential.html` — long, sequential argument
White, navy, Source Serif headlines, editorial spacing. Reads like a document that gets forwarded to a CFO.

Headline: *"Still comparing mobile app developers by the hour?"*

Uses the “Questioning the Mistake” direct-response structure, then makes the sequential argument:
problem → why hourly billing misaligns incentives → the three commitments → public-safety proof → who
it's for and not for → what happens on the call → form → FAQ. CTA repeats at every stopping point.

Best fit for colder traffic and for buyers who need to justify the decision to someone else.

### Both pages
- Four form fields: name, work email, phone, "what are you trying to fix"
- **Budget field removed entirely.** It was required on the old page with "Under $25,000" as an option —
  asking the visitor to reveal budget while giving nothing back, before any trust exists.
- CAPTCHA removed. Use a honeypot or invisible challenge instead.
- No nav menu. Phone reachable throughout, sticky on mobile for page A.
- Tailwind via CDN is intentional for these portable review prototypes.

---

## Tracking spec

```javascript
dataLayer.push({ event: 'form_start',  form_id: 'b3_lp_a' });  // or b3_lp_b
dataLayer.push({ event: 'form_submit', form_id: 'b3_lp_a' });
dataLayer.push({ event: 'phone_click', phone_location: 'hero' }); // top_bar | form_card | sticky_mobile
```

- GTM: fire GA4 `generate_lead` off `form_submit`. Separate event off `phone_click`.
- Turn OFF GA4 Enhanced Measurement form interactions to avoid double-counting.
- Fire server-side conversions from the API route, passing the browser `event_id` for dedupe.
- Never push PII into the dataLayer.

The existing conversion action is named "Submit lead form." Keep the naming consistent or update it
in the account when these go live.

---

## Build notes

The current HTML files are portable review prototypes. Their forms intentionally demonstrate layout
and tracking intent only; they do not submit leads. After the direction is approved, another party will
rebuild the selected concept in the client's WordPress/Elementor environment and handle production
forms, spam protection, performance, tracking implementation, and QA.

---

## What to do in the account, regardless of which page wins

Ranked by impact:

1. **Add negatives.** spotify, "how to", tutorial, freelance, "for hire", cheap, diy. Kills ~30% of waste immediately.
2. **Rewrite the RSA.** Drop the three headlines listed above. Add: fixed price, fixed date, one-year
   warranty, Pittsburgh engineers, trusted by police departments. The ad and the page must promise the
   same thing — that mismatch is what's producing the below-average landing page experience scores.
3. **Ship the new page.** Quality Score should follow, which lowers CPC and recovers some of the 47.51%
   impression share lost to rank.
4. **Restructure keywords.** The current set buys generic app-development intent, which attracts app-idea
   people. `[field service app development]` got 2 impressions in 30 days — the operational angle isn't
   being bought at all. Consider a second ad group around field operations, work order management,
   and mobile workforce terms, which is where their actual case studies live.
5. **Budget.** 35.13% of impression share is lost to budget at $80/day. Don't raise it until the page
   and the negatives are fixed — no point buying more of the wrong traffic.

### The math if the page works

Same spend, same CPC, conversion rate goes from 0.81% to 3% (still under the LP median):

123 clicks × 3% = 3.7 leads at roughly **$485 per lead instead of $1,795**.

Before any Quality Score improvement, which would add clicks on the same budget.

---

## Test order once live

1. A vs B — structure. This is the primary test.
2. Message match: ad headline vs page headline. Biggest documented lever in the research (+212.74% in
   the Disruptive/Moz case).
3. Form: 4 fields vs 3 (drop phone). Watch lead quality, not just volume — this is B2B, so fewer
   better leads may win.
4. Proof placement on page B: public-safety block above the mechanism vs below it.
5. CTA copy: "Get My Fixed-Fee Estimate" vs "Request an Estimate" vs "See What It Would Cost."

Do not test design polish (colors, button shapes) until the above are settled. They move the needle least.
