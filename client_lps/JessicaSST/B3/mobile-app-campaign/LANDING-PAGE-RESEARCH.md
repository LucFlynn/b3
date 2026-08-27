# Lead-Gen Landing Page Reference

Portable reference for building lead-gen landing pages. Drop this into a repo or paste into another session as context.

Owner: Luc Flynn / Electro Raven. Stack: Astro or Next on Vercel, server-side tracking via GTM, GA4, Meta CAPI.

Scope: lead gen only. Three page types — local service quote, B2B demo/consult booking, webinar/VSL opt-in. No ecommerce, no product pages, no SaaS trial flows.

---

# Part 1 — The three frameworks

Three different jobs. MECLABS decides section order. Hormozi writes the offer. CXL decides what gets cut.

## MECLABS Conversion Sequence Heuristic

`C = 4m + 3v + 2(i − f) − 2a`

- **m — motivation (weight 4).** The biggest factor and the one you control least. You buy it with targeting. A page can't create motivation in someone who doesn't have the problem.
- **v — value proposition clarity and force (weight 3).** The thing you control most. Belongs in the headline.
- **i — incentive.** Something that offsets friction you can't remove.
- **f — friction.** Two kinds: length friction (steps, fields) and difficulty friction (confusion, ambiguity).
- **a — anxiety (weight −2).** Psychological concern about handing over info or being let down.

MECLABS states plainly that this is not an equation to solve — it's a thought tool and a checklist. The coefficients signal relative importance, not literal math. Don't score pages numerically.

**Order rule:** win motivation and value before touching incentive, friction, or anxiety. Discounting a page nobody understands doesn't work.

### The 8 micro-yeses

McGlaughlin frames the page as a conversation, not a layout. "We do not design a web page, we design a cognitive progression."

| Stage | Yes | The question in their head |
|---|---|---|
| Connect | 1 | Will I pay attention? *(headline's job)* |
| Connect | 2 | Will I engage further? *(subhead's job)* |
| Explain | 3 | Do I understand this? |
| Explain | 4 | Do I believe it? |
| Persuade | 5 | Do I want this now? |
| Persuade | 6 | Do I want it from **you**? |
| Exchange | 7 | Will I trade for it? |
| Exchange | 8 | Will I finish? |

One "no" kills every yes before it. Two more McGlaughlin rules worth keeping:
- **"Clarity trumps persuasion."**
- **The "why" doesn't matter before the "what."** Say what the thing is before you say why it's good.

## Hormozi Value Equation

`Value = (Dream Outcome × Perceived Likelihood of Achievement) ÷ (Time Delay × Effort & Sacrifice)`

Raise the top two, shrink the bottom two. Critical detail: it's all **perceived**. If you don't communicate it on the page, you don't get paid for it.

Maps to page blocks like this:

| Variable | Where it lives on the page |
|---|---|
| Dream Outcome | Headline |
| Perceived Likelihood | Proof, case studies, guarantee |
| Time Delay | "How fast" — timeframes, response windows |
| Effort & Sacrifice | "How easy" — process steps, we-handle-it copy |

### Grand Slam Offer stack

Dream outcome → decompose every sub-problem and solve each → named bonuses with dollar values → guarantee → scarcity/urgency → naming and pricing.

### Guarantee types

- **Unconditional** — money back, no questions.
- **Conditional** — do X, Y, Z and if no result, refund. Hormozi's preference for higher ticket.
- **Anti-guarantee** — all sales final, positioned as exclusivity.
- **Implied** — performance or revenue share.

You can stack them. For B2B services, removing contract lock-in often beats offering money back, because the fear is the 12-month commitment, not the price.

### Naming: MAGIC

Magnetic reason why + Avatar + Goal + Interval + Container word.
Example shape: "Free 6-Week Lean-By-Halloween Challenge."

### Lead magnets

A complete solution to a **narrow** problem, which reveals a bigger problem the core offer solves. Three types: reveal a problem (diagnosis), a sample or trial, or one step of a multi-step process.

For B2B consult pages, treat the call itself as the lead magnet. Give away something they keep regardless.

## CXL / Peep Laja

- **ResearchXL model:** CRO is roughly 80% research, 20% testing.
- **Heuristic audit, four dimensions:** Clarity, Relevancy (message match), Friction, Anxiety/Distraction. Audit desktop and mobile separately.
- **"Clarity trumps persuasion."**
- **Message match / scent:** the ad they clicked needs to smell like the page they land on. Break scent and you lose a click you already paid for.
- **Above the fold** is a default, not a law. CXL documented a test where moving the CTA to the bottom of a long page lifted conversions 304%.
- **Social proof in three layers:** client logos and counts above the fold (low reading cost) → detailed testimonials mid-page after benefits → badges and guarantee near the form.
- **CXL eye-tracking:** testimonials with photos and real client logos are the most memorable.
- **Grade proof with CRAVENS** (Angie Schottmuller): Credible, Relevant, Attractive, Visual, Enumerated, Nearby, Specific.

## Supporting research

**Form fields.** Unbounce data shows conversion falling non-linearly as fields grow; three is a repeated sweet spot and the steepest drop sits between four and seven. Multi-step forms tend to beat single-page forms with the same total field count. Baymard's finding for complex forms: *perceived* field count matters more than raw count — logical grouping and stepping make a form feel smaller.

**Reading behavior (NN/g).** People scan, they don't read. F-pattern (two horizontal sweeps plus a left vertical) and the layer-cake pattern (eyes bounce along headings, skipping body copy). From "How Little Do Users Read?": on an average page users have time to read at most 28% of the words, and 20% is more likely (based on Weinreich et al., ACM Transactions on the Web, 2008; 25 users, ~50,000 pageviews).

Implication: **headings alone have to carry the argument.** Write descriptive subheads, front-load the left edge, put the value prop in the headline.

---

# Part 2 — Where the frameworks disagree

Important because Luc buys both cold Meta and high-intent Google.

**Long-form stacking (Hormozi) vs. minimalism (CXL).** Hormozi stacks value, bonuses, and proof until the offer is overwhelming. CXL wants the fewest words that produce clarity. MECLABS splits it: length itself isn't friction, *unnecessary* length is. A long page is fine if every added block raises value or lowers anxiety.

Settle it with traffic temperature:

| | Cold Meta | High-intent Google |
|---|---|---|
| Lean | Hormozi | CXL |
| Page length | Longer | Short |
| Why | Motivation doesn't exist yet — the page manufactures it | Motivation already exists — don't slow them down |
| Emphasis | Problem agitation, proof, stacking | Message match, speed, path to CTA |

**Hype vs. clarity.** Never let a claim outrun the proof. A big promise with weak proof *raises* anxiety and kills micro-yes #4. Cold traffic tolerates more emotion. B2B and regulated verticals tolerate much less.

**CTA above the fold vs. where conviction peaks.** High-intent/action pages: CTA up top and repeated. Cold or considered pages: CTA where the argument lands, then repeated at every logical stopping point for layer-cake scanners.

**Minimize fields vs. qualify.** More fields means fewer, better leads. By archetype: local = volume (the phone call qualifies), B2B = quality (protect the calendar), webinar = volume (the event qualifies). Don't blindly cut — a VWO case (Blivakker) showed the lighter form losing when it dropped fields the business actually needed.

**Practical upshot:** build two variants of every offer if the client buys both channels.

---

# Part 3 — Archetype A: Local service quote

Plumbing, HVAC, roofing, mold, cleaning. High intent, "near me," phone-heavy.

**The situation.** They have the problem right now. Motivation is already high. The job is almost entirely value clarity, friction, and anxiety. Keep it short.

**Section order and why:**

1. **Sticky top bar with tap-to-call.** Friction and anxiety. High-intent local buyers call more than they type. Phone must be reachable in the thumb zone the whole scroll.
2. **Hero: headline + subhead + trust line + dual CTA.** Micro-yes 1 and 2, plus message match. Headline echoes the ad and keyword (service, city, "near me"). Dual CTA because local traffic splits into callers and form-fillers — pick one and you lose half.
3. **Trust strip — licensed, insured, years, rating.** Anxiety reduction plus CXL's logos-above-the-fold rule. Four proof points at low reading cost.
4. **"What you get" — 3 to 4 bullets.** Dream outcome and perceived likelihood; micro-yes 3. Write one bullet per value-equation lever, not four bullets about the company.
5. **Short form (3–4 fields) or call.** The macro-yes. Name, phone, ZIP.
6. **Guarantee.** Conditional or implied. Specific consequence, not "satisfaction guaranteed."
7. **Two local reviews with names.** CRAVENS — nearby and specific. Make each review beat a *different* objection.
8. **3-step process.** Cuts effort and time delay. Three steps, never five.
9. **Service area / map + repeat CTA.** Confirms "near me," catches scanners.
10. **Sticky mobile bottom call bar.**

**Copy shapes:**

- Headline: `[SERVICE] in [CITY] — [SPEED/OUTCOME PROMISE]`
- Subhead: `[Licensed & insured] [trade]s fixing [PROBLEM] for [CITY] homeowners since [YEAR]. No-obligation quote.`
- Trust strip: Licensed & Insured · `[X]` Years in `[CITY]` · `[X.X]` stars from `[N]` reviews · `[Guarantee]`
- Bullets: free first step / upfront pricing no surprise fees / `[same-day]` scheduling / warranty on all work
- Button: `Get My Free [SERVICE] Quote`
- Microcopy: `No obligation. We reply within [TIME]. Your info is never sold.`
- Guarantee: `If we don't [OUTCOME] by [TIME], [CONSEQUENCE].`
- Review: `"[specific result + speed]" — [First Name], [Neighborhood]`

**Field rule:** 3, max 4. Add a fourth only if it changes who you dispatch.

**Test order:** message match → form vs. call-first weighting → first-person CTA copy → field count → guarantee wording.

---

# Part 4 — Archetype B: B2B demo / consult booking

Agency services, software demos, strategy calls.

**The situation.** Moderate, rational motivation. The fight is differentiation, anxiety about wasting 30 minutes, and perceived likelihood. Longer page is fine and often better. Primary CTA stays reachable throughout.

**Section order and why:**

1. **Minimal top bar — logo plus one CTA.** Aim for a 1:1 attention ratio. Every nav link is an exit.
2. **Hero: outcome headline + subhead + CTA + client logo row.** Micro-yes 1 and 2, dream outcome, logos above fold. Name the avatar — it filters better than any qualifier field.
3. **Problem agitation into outcome bridge.** Problem decomposition; micro-yes 3 and 4. Naming the problem more precisely than competitors is what makes them believe you can solve it.
4. **"What you'll get on the call."** Highest-leverage block on the page. Converts a vague time commitment into a concrete deliverable. Include something they keep regardless of whether they buy.
5. **Proof: metrics plus 2–3 case studies with names, logos, numbers.** CRAVENS; micro-yes 6.
6. **Differentiator / how we're different.** The value variable — appeal plus exclusivity.
7. **Booking block: calendar embed or 3–5 field form plus one qualifier.**
8. **Risk reversal — conditional or implied, plus a "no pitch" promise.**
9. **Founder/team credibility, testimonial wall.**
10. **FAQ handling objections, then final CTA.**

**Copy shapes:**

- Headline: `[DREAM OUTCOME] for [AVATAR] — without [PAIN]`
- Subhead: `We help [AVATAR] [OUTCOME] using [MECHANISM]. Book a free [CALL TYPE] — no pitch.`
- Button: `Book My Free [CALL TYPE]`
- On the call: custom audit of your `[X]` / `[deliverable]` you keep either way / `[N]`-point breakdown / straight answers, no hard sell
- Proof metric: `[NUMBER][unit] [outcome]` across `[N]` clients
- Case study: `[CLIENT]` went from `[BEFORE]` to `[AFTER]` in `[TIMEFRAME]`
- Differentiator: `Unlike [alternative], we [MECHANISM] so you [BENEFIT]`
- Guarantee: `Month to month. If we don't [beat metric] in [time], you don't pay for [thing].`
- FAQ must cover: price, who does the work, contract length, "will this work for my industry"

**Field rule:** 3–5 plus exactly one qualifier (dropdown, not open text). This is the deliberate exception to "cut every field" — a bad-fit call costs 30 minutes, a good-fit call is worth thousands. Two qualifiers is greedy.

**Calendar vs. form:** embed cuts time delay and books more calls; form qualifies harder and books fewer. Depends on whether the bottleneck is volume or calendar.

**Test order:** remove nav → value-prop headline → calendar vs. qualifier form → proof placement and type → first-person CTA.

---

# Part 5 — Archetype C: Webinar / VSL opt-in

**The situation.** Usually cold-to-warm Meta plus email. Motivation has to be manufactured on the page with a specific, curiosity-driven promise. Fight is headline specificity, friction (2–3 fields), and perceived likelihood.

**Real KPI is registration × show-up, not registration.** Only 40–56% of registrants typically attend.

**Section order and why:**

1. **Eyebrow: date, time, "free," format.** Answers "what is this and what will it cost me" before the headline. Hiding the time commitment doesn't get more signups, it gets more no-shows.
2. **Hero headline + curiosity subhead + inline 2–3 field form.** Form goes up top because the ask is tiny. Opposite of the B2B page, where the ask is big and proof comes first.
3. **"In this training you'll discover" — 3 to 5 curiosity bullets.** Each one opens a loop the training closes. Never write a bullet that fully answers itself.
4. **Host credibility — photo, one line of hard proof.** Cold traffic needs this or a big claim from an unknown face reads as hype and *raises* anxiety.
5. **Social proof: attendee count plus a testimonial.** Best testimonials describe something that happened *during* the session.
6. **Payoff plus who it's for / not for.** The "not for" half filters no-shows and raises the perceived level of the room. Counterintuitively lifts registrations too.
7. **Repeat form/CTA plus real urgency.** Real seats or a real deadline. A countdown that resets on refresh gets noticed and costs trust permanently.
8. **Separate confirmation page.** This is the show-up system, not a nicety.

**Copy shapes:**

- Eyebrow: `FREE [LIVE] [TRAINING] · [DATE] at [TIME ZONE]`
- Headline: `How to [OUTCOME] in [TIMEFRAME] — Even If [OBJECTION]`
- Subhead: `Join [HOST] and learn the exact [MECHANISM] behind [RESULT]. Free, live, [DURATION].`
- Button: `Save My Free Seat`
- Bullet shapes: the `[#1 mistake]` and the 2-minute fix / why `[common advice]` is wrong / how to `[OUTCOME]` even if `[OBJECTION]` / the exact `[tool/template]` we use, yours to keep
- Host bio: `[HOST] has [PROOF] in [FIELD]` — one line of hard proof, not a bio
- Urgency: `Only [N] live seats` / `Registration closes [DATE]`
- Confirmation page: "You're in." + add-to-calendar button (make it the biggest thing) + what to bring + restate payoff + where the link arrives

**Field rule:** 2. Not three, definitely not five. The event qualifies people; qualifying twice costs volume for nothing. Ask for company or role on the confirmation page, after commitment.

**Reminder sequence:** immediately, 24h out, 1h out, "we're live now."

**Test order:** headline clarity vs. curiosity → field count → social proof on/off and type → first-person CTA → confirmation and reminder sequence.

---

# Part 6 — Test priority with documented effect sizes

Same top levers across all three archetypes. Run one variable at a time.

| Rank | Test | Documented result | Source |
|---|---|---|---|
| 1 | Message match to the ad | +212.74% conversion rate, −69.39% cost per conversion | Disruptive Advertising, published on Moz |
| 2 | Value-prop headline rewrite | +54% and +87.61% | MECLABS / MarketingExperiments |
| 3 | Remove nav / attention ratio | +16% and +28% on MOFU pages | HubSpot's own test |
| 3b | Remove nav + form above fold | 3.12% → 13.64% (+336%) | Career Point College, via Unbounce |
| 3c | Remove main nav | 3% → 6% | Yuppiechef, via VWO |
| 4 | First-person CTA ("my" vs "your") | +90% CTR | Michael Aagaard / ContentVerve |
| 5 | Field count 4 → 3 | ~+50% | HubSpot data |
| 6 | Testimonial with client logo | +69% leads | comScore, via Optimizely |
| — | CTA moved to bottom of long page | +304% | CXL |
| — | Webinar headline with all four elements | +34% | Sequel.io, 47 variations tested |

**Caveat that matters:** several of these are 10+ years old (ContentVerve ~2013, HubSpot field studies ~2010–2012, comScore). Modern tests show the form-field effect has flattened. Treat every percentage as "worth testing," not "will happen to you."

**Benchmarks to judge a page against:**
- Unbounce Q4 2024 Conversion Benchmark Report: 6.6% median across all industries. Based on 57M conversions, 41,000+ landing pages, 464M visitors. SaaS lowest at 3.8%, Events/Entertainment highest at 12.3%.
- WordStream/LocaliQ Google Ads median: 2.35%. Top 25% of accounts hit 5.31%+, top 10% hit 11.45%.

These measure different things — Unbounce measures purpose-built landing pages, WordStream measures Google Ads destination pages across accounts. Don't hold one to the other's number.

**Thresholds that change the plan:**
- Clicks but >80% bounce on paid traffic → message-match problem. Fix the hero headline before anything else.
- Registrations high, show-up under 40% → stop touching the page, fix the confirmation and reminder sequence.
- B2B lead volume fine, quality bad → *add* a qualifier field. Reverse the minimize-fields rule.
- Local quote volume low but calls strong → make the page phone-first, shrink or drop the form.

---

# Part 7 — Tracking spec

Standard dataLayer structure across all three archetypes:

```javascript
// form start — first focus into any field
dataLayer.push({ event: 'form_start', form_id: 'local_quote' }); // or b2b_demo / webinar_optin

// form submit — on successful submit
dataLayer.push({ event: 'form_submit', form_id: 'local_quote' });

// phone click — pass which button fired it
dataLayer.push({ event: 'phone_click', phone_location: 'hero' }); // top_bar | sticky_mobile

// booking complete — calendar embed success callback
dataLayer.push({ event: 'booking_complete', form_id: 'b2b_demo' });

// VSL only — for retargeting partial viewers
dataLayer.push({ event: 'video_progress', percent: 50 });
```

**GTM configuration:**
- Fire a GA4 `generate_lead` tag off `form_submit` and `booking_complete`. It's a GA4 recommended event and auto-flags as a Key Event.
- Separate GA4 event off `phone_click`.
- **Turn off GA4 Enhanced Measurement's automatic form interactions** or you'll double-count.

**Server side:**
- Fire Meta CAPI `Lead` / `Schedule` / `CompleteRegistration` from the API route or the calendar webhook, not the browser.
- Pass the same `event_id` generated in the browser so Meta dedupes browser and server events.
- Calendar webhooks are more reliable than browser callbacks for B2B booking.

**Never push PII** — name, email, phone — into the dataLayer. Hash and send server-side only.

---

# Part 8 — Build notes

**Astro.** Component per archetype in `src/components/`. Copy variables become frontmatter props:

```astro
---
const { service, city, phone } = Astro.props;
---
<h1>{service} in {city}</h1>
```

**React / Next.** `class` → `className`, `for` → `htmlFor`. Inline `on*` handlers become functions calling `window.dataLayer.push()`. Form is controlled, POSTs to an API route, which fires CAPI server-side.

**Both.** Mobile-first, semantic HTML, real `<label>` elements tied to inputs, correct `type` and `inputmode` so the right mobile keyboard opens (`tel`, `email`, `numeric`). No external dependencies beyond Tailwind. No autoplay video. Target LCP under 2.5s on 4G.

**Free libraries worth borrowing structure from:**

| Library | License | Use for |
|---|---|---|
| HyperUI (hyperui.dev) | MIT | Tailwind section blocks, copy-paste |
| Flowbite | MIT | Forms, modals, datepickers |
| AstroWind | MIT | Best MIT Astro starter, near-perfect PageSpeed |
| Accessible Astro Starter | MIT | WCAG-focused base |
| Astroship | GPL-3.0 | Fine hosted, careful redistributing |
| Tailwind UI free tier | Paid/per-seat | Accessible form patterns |

MIT: do what you want, keep the notice. GPL-3.0: fine for hosted client sites, don't redistribute closed modifications.

---

# Part 9 — Pre-launch QA

Run on every page before it takes traffic.

1. Hero headline uses the same words as the ad or keyword
2. Stranger can state what you do, where, and the next step in 5 seconds
3. Field count matches the archetype rule
4. `type` and `inputmode` set correctly on every input
5. Anxiety handled: guarantee, proof with real names, privacy line near the form
6. No nav menu, no outbound links except the phone
7. LCP under ~2.5s on 4G, images compressed to WebP
8. Primary CTA reachable in the mobile thumb zone
9. `form_start`, `form_submit`, `phone_click` all fire in GTM Preview and GA4 DebugView
10. Server event dedupes with browser `event_id` in Meta Events Manager

---

# Caveats

- The heuristic is a checklist, not math. MECLABS says so explicitly. Don't score pages numerically.
- Case-study effect sizes are directional. Many are old and context-specific.
- Some supporting stats came from secondary aggregators rather than original studies — particularly some field-count percentages and webinar averages. The framework spine (MECLABS pages, Hormozi's books, CXL's own research) and the primary case studies (Optimizely/comScore, HubSpot nav test, Disruptive via Moz, MarketingExperiments value-prop tests, NN/g eye-tracking) are the reliable core.
