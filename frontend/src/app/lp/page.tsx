import Link from "next/link";

// ── Mock UI Components ──

function MockBrowser({
  children,
  url,
}: {
  children: React.ReactNode;
  url?: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-700/50 bg-white shadow-2xl shadow-emerald-500/5 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-zinc-100 border-b border-zinc-200">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-400/80" />
          <div className="w-3 h-3 rounded-full bg-green-400/80" />
        </div>
        <div className="flex-1 text-center">
          <div className="inline-block bg-white rounded-md px-4 py-1 text-xs text-zinc-400 border border-zinc-200">
            {url || "epi.lucflynn.com/dashboard"}
          </div>
        </div>
      </div>
      <div className="bg-zinc-50 text-zinc-900">{children}</div>
    </div>
  );
}

function MockCheckRow({
  ok,
  label,
  value,
  points,
  running,
}: {
  ok: boolean | null;
  label: string;
  value: string;
  points?: number;
  running?: number;
}) {
  const icon = ok === true ? "\u2713" : ok === false ? "\u2717" : " ";
  const iconColor =
    ok === true
      ? "text-green-600"
      : ok === false
        ? "text-red-500"
        : "text-transparent";
  const valueColor =
    ok === true
      ? "text-green-600"
      : ok === false
        ? "text-red-500"
        : "text-zinc-400";

  return (
    <div className="flex items-center justify-between text-[11px] sm:text-sm py-1.5 border-b border-zinc-100 px-2">
      <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
        <span className={`w-3 sm:w-3.5 shrink-0 text-center ${iconColor}`}>
          {icon}
        </span>
        <span className="text-zinc-700">{label}</span>
      </div>
      <div className="flex items-center gap-2 sm:gap-3 shrink-0 ml-2 sm:ml-4">
        <span className={`text-[11px] sm:text-sm ${valueColor}`}>{value}</span>
        {points != null && (
          <span
            className={`font-mono text-[10px] sm:text-xs w-8 sm:w-10 text-right ${points > 0 ? "text-green-600" : "text-red-500"}`}
          >
            {points > 0 ? "+" : ""}
            {points}
          </span>
        )}
        {running != null && (
          <span className="text-zinc-400 text-[10px] sm:text-xs w-8 sm:w-10 text-right font-mono">
            {"\u2192"} {running}
          </span>
        )}
      </div>
    </div>
  );
}

function MockScoreBreakdown() {
  return (
    <div className="border-t border-zinc-200 bg-zinc-50 px-3 sm:px-4 py-3 sm:py-4">
      <div className="flex items-start justify-between mb-3 sm:mb-4">
        <div>
          <p className="text-sm sm:text-base font-semibold text-zinc-900">
            sales.inquiry@tmpmail.org
          </p>
          <p className="text-[11px] sm:text-sm text-zinc-500 mt-0.5">
            Score: 0 —{" "}
            <span className="uppercase text-red-600 font-medium">junk</span>
            {" \u00B7 "}Mar 6, 2026 11:05 AM
          </p>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-700">
          0 junk
        </span>
      </div>

      <p className="text-[10px] sm:text-xs text-zinc-400 mb-1.5">
        What We Found
      </p>
      <MockCheckRow ok={false} label="Email" value="disposable" />
      <MockCheckRow
        ok={false}
        label="Phone"
        value="(555) 000-0000 \u00B7 invalid"
      />
      <MockCheckRow ok={false} label="Honeypot" value="triggered" />
      <MockCheckRow
        ok={false}
        label="Form fill time"
        value="0.4s \u00B7 too fast"
      />
      <MockCheckRow ok={false} label="IP" value="datacenter" />
      <MockCheckRow ok={false} label="VPN/Proxy" value="yes" />
      <MockCheckRow ok={null} label="Attribution" value="none" />

      <p className="text-[10px] sm:text-xs text-zinc-400 mb-1.5 mt-3">Score</p>
      <div className="flex items-center justify-between text-[11px] sm:text-sm text-zinc-400 py-1.5 border-b border-zinc-200 bg-zinc-100/50 px-2 rounded-t">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="w-3 sm:w-3.5" />
          <span>Baseline</span>
        </div>
        <span className="font-mono text-[10px] sm:text-xs w-8 sm:w-10 text-right">
          50
        </span>
      </div>
      <MockCheckRow
        ok={false}
        label="Disposable email"
        value=""
        points={-15}
        running={35}
      />
      <MockCheckRow
        ok={false}
        label="Invalid phone"
        value=""
        points={-15}
        running={20}
      />
      <MockCheckRow
        ok={false}
        label="Honeypot triggered"
        value=""
        points={-30}
        running={0}
      />
      <MockCheckRow
        ok={false}
        label="Bot timing (0.4s)"
        value=""
        points={-5}
        running={0}
      />
      <MockCheckRow
        ok={false}
        label="Datacenter IP"
        value=""
        points={-15}
        running={0}
      />
      <MockCheckRow
        ok={false}
        label="VPN detected"
        value=""
        points={-10}
        running={0}
      />
      <div className="flex items-center justify-between text-[11px] sm:text-sm font-semibold text-zinc-900 py-1.5 bg-zinc-100/50 px-2 rounded-b">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="w-3 sm:w-3.5" />
          <span>Final</span>
        </div>
        <span className="font-mono text-[10px] sm:text-xs w-8 sm:w-10 text-right text-red-600">
          0
        </span>
      </div>
    </div>
  );
}

function MockLeadRow({
  score,
  label,
  email,
  source,
  time,
  flags,
}: {
  score: number;
  label: string;
  email: string;
  source?: string;
  time: string;
  flags?: string[];
}) {
  const colors: Record<string, string> = {
    verified: "bg-green-100 text-green-700",
    likely_real: "bg-lime-100 text-lime-700",
    suspicious: "bg-orange-100 text-orange-700",
    junk: "bg-red-100 text-red-700",
  };
  return (
    <div className="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 border-b border-zinc-100 last:border-0">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 sm:px-2.5 py-0.5 text-[10px] sm:text-xs font-medium ${colors[label] || "bg-zinc-100 text-zinc-500"}`}
          >
            {score} {label.replace("_", " ")}
          </span>
          <span className="truncate text-xs sm:text-sm font-medium text-zinc-900">
            {email}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-[10px] sm:text-xs text-zinc-400">
          {source && <span>{source}</span>}
          <span>{time}</span>
        </div>
        {flags && flags.length > 0 && (
          <div className="mt-0.5 text-[10px] sm:text-xs text-orange-600">
            Flags: {flags.join(" \u00B7 ")}
          </div>
        )}
      </div>
      <span className="text-zinc-300 text-xs ml-2">{"\u25BC"}</span>
    </div>
  );
}

function MockLeadFeed() {
  return (
    <div>
      <div className="flex items-center gap-3 px-3 sm:px-4 py-2 text-[10px] sm:text-xs text-zinc-500 border-b border-zinc-100 flex-wrap">
        <span>
          Total: <strong className="text-zinc-700">47</strong>
        </span>
        <span className="text-green-600">Verified: 19</span>
        <span className="text-lime-600">Likely Real: 14</span>
        <span className="text-orange-600">Suspicious: 8</span>
        <span className="text-red-600">Junk: 6</span>
      </div>
      <MockLeadRow
        score={91}
        label="verified"
        email="sarah.c@acmecorp.com"
        source="Google Ads"
        time="Mar 6, 2:14 PM"
      />
      <MockLeadRow
        score={67}
        label="likely_real"
        email="mike.r@gmail.com"
        source="Meta Ads"
        time="Mar 6, 1:47 PM"
        flags={["voip phone"]}
      />
      <MockLeadRow
        score={42}
        label="suspicious"
        email="j.martinez@yahoo.com"
        source="organic"
        time="Mar 6, 12:33 PM"
        flags={["voip", "VPN"]}
      />
      <MockLeadRow
        score={8}
        label="junk"
        email="info@tempmail.xyz"
        time="Mar 6, 11:05 AM"
        flags={["bot", "disposable email", "datacenter IP"]}
      />
    </div>
  );
}

// ── Full Score Breakdown (Section 4 — different lead, mixed signals) ──

function MockMixedScoreBreakdown() {
  return (
    <div className="border-t border-zinc-200 bg-zinc-50 px-3 sm:px-4 py-3 sm:py-4">
      <div className="flex items-start justify-between mb-3 sm:mb-4">
        <div>
          <p className="text-sm sm:text-base font-semibold text-zinc-900">
            david.n@gmail.com
          </p>
          <p className="text-[11px] sm:text-sm text-zinc-500 mt-0.5">
            Score: 45 —{" "}
            <span className="uppercase text-orange-600 font-medium">
              suspicious
            </span>
            {" \u00B7 "}Mar 6, 2026 3:22 PM
          </p>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-orange-100 text-orange-700">
          45 suspicious
        </span>
      </div>

      <p className="text-[10px] sm:text-xs text-zinc-400 mb-1.5">
        What We Found
      </p>
      <MockCheckRow ok={true} label="Email" value="valid" />
      <MockCheckRow
        ok={false}
        label="Phone"
        value="(505) 555-0192 \u00B7 voip"
      />
      <MockCheckRow ok={true} label="Honeypot" value="clean" />
      <MockCheckRow ok={true} label="Form fill time" value="6.4s" />
      <MockCheckRow ok={false} label="IP" value="datacenter" />
      <MockCheckRow ok={false} label="VPN/Proxy" value="yes" />
      <MockCheckRow ok={true} label="Attribution" value="Google Ads click" />

      <p className="text-[10px] sm:text-xs text-zinc-400 mb-1.5 mt-3">Score</p>
      <div className="flex items-center justify-between text-[11px] sm:text-sm text-zinc-400 py-1.5 border-b border-zinc-200 bg-zinc-100/50 px-2 rounded-t">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="w-3 sm:w-3.5" />
          <span>Baseline</span>
        </div>
        <span className="font-mono text-[10px] sm:text-xs w-8 sm:w-10 text-right">
          50
        </span>
      </div>
      <MockCheckRow
        ok={true}
        label="Valid email"
        value=""
        points={20}
        running={70}
      />
      <MockCheckRow
        ok={false}
        label="VOIP phone"
        value=""
        points={-5}
        running={65}
      />
      <MockCheckRow
        ok={true}
        label="Google Ads click ID"
        value=""
        points={10}
        running={75}
      />
      <MockCheckRow
        ok={true}
        label="Human timing (6.4s)"
        value=""
        points={5}
        running={80}
      />
      <MockCheckRow
        ok={false}
        label="Datacenter IP"
        value=""
        points={-15}
        running={65}
      />
      <MockCheckRow
        ok={false}
        label="VPN detected"
        value=""
        points={-10}
        running={55}
      />
      <MockCheckRow
        ok={false}
        label="Duplicate (2x)"
        value=""
        points={-10}
        running={45}
      />
      <div className="flex items-center justify-between text-[11px] sm:text-sm font-semibold text-zinc-900 py-1.5 bg-zinc-100/50 px-2 rounded-b">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <span className="w-3 sm:w-3.5" />
          <span>Final</span>
        </div>
        <span className="font-mono text-[10px] sm:text-xs w-8 sm:w-10 text-right text-orange-600">
          45
        </span>
      </div>

      <div className="mt-3 text-[10px] sm:text-xs text-zinc-400 space-y-0.5 px-2">
        <p>
          <span className="text-green-600">{"\u2713"}</span> Google click ID{" "}
          <span className="text-zinc-400">CjwKCAjw...copy</span>
        </p>
        <p className="text-zinc-500">Source: google {"\u00B7"} Medium: cpc</p>
        <p className="text-zinc-500">Campaign: search_brand_q1</p>
      </div>
    </div>
  );
}

// ── Page Sections ──

function Hero() {
  return (
    <section className="min-h-screen flex items-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(16,185,129,0.08),transparent)]" />
      <div className="max-w-6xl mx-auto px-5 sm:px-6 py-16 sm:py-20 relative z-10 w-full">
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          <div>
            <h1 className="font-[family-name:var(--font-display)] text-3xl sm:text-4xl md:text-5xl lg:text-[3.5rem] font-bold tracking-tight leading-[1.1]">
              Your ad platforms are lying about your leads.
              <br />
              <span className="text-emerald-400">
                We check 7 things they won{"'"}t.
              </span>
            </h1>
            <p className="mt-5 sm:mt-6 text-base sm:text-lg text-zinc-400 leading-relaxed max-w-xl">
              EPI scores every lead that hits your forms — checking email
              validity, phone type, bot behavior, IP intelligence, duplicates,
              form timing, and ad attribution. You see the math on every score.
            </p>
            <div className="mt-7 sm:mt-8 flex flex-col sm:flex-row gap-4">
              <Link
                href="/sign-up"
                className="inline-flex items-center justify-center rounded-lg bg-emerald-500 px-7 py-3.5 text-base font-semibold text-white hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20"
              >
                Start scoring free — 100 leads on us
              </Link>
              <a
                href="#pricing"
                className="inline-flex items-center justify-center rounded-lg border border-zinc-700 px-6 py-3.5 text-sm font-medium text-zinc-300 hover:border-zinc-500 hover:text-white transition"
              >
                See pricing
              </a>
            </div>
            <p className="mt-6 text-sm text-zinc-500">
              Built by a media buyer who{"'"}s managed $11M+ in ad spend across
              200+ accounts.
            </p>
          </div>
          <div className="relative lg:pl-4">
            <div className="transform lg:rotate-1 lg:translate-x-4">
              <MockBrowser>
                <MockScoreBreakdown />
              </MockBrowser>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Problem() {
  const blocks = [
    {
      lines: [
        "Google says you got 150 leads.",
        "Your CRM has 43 real contacts.",
        "Where did 107 leads go?",
      ],
    },
    {
      lines: [
        "Display network inflates your numbers.",
        "Bots fill out your forms.",
        "Duplicate submissions get counted twice.",
      ],
    },
    {
      lines: [
        "Your agency reports CPL on the fake number.",
        "You make decisions on data that\u2019s lying to you.",
        "Every optimization downstream is wrong.",
      ],
    },
  ];

  return (
    <section className="py-20 sm:py-28 border-t border-zinc-800/50">
      <div className="max-w-5xl mx-auto px-5 sm:px-6">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-center">
          The lead quality problem nobody talks about
        </h2>
        <div className="mt-12 sm:mt-16 grid md:grid-cols-3 gap-8 md:gap-6">
          {blocks.map((block, i) => (
            <div
              key={i}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 sm:p-8"
            >
              {block.lines.map((line, j) => (
                <p
                  key={j}
                  className={`text-base sm:text-lg leading-relaxed ${j === block.lines.length - 1 ? "text-white font-semibold mt-3" : "text-zinc-400"}`}
                >
                  {line}
                </p>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="py-20 sm:py-28 border-t border-zinc-800/50">
      <div className="max-w-5xl mx-auto px-5 sm:px-6">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-center">
          Install in 5 minutes. Score every lead automatically.
        </h2>

        <div className="mt-14 sm:mt-20 space-y-16 sm:space-y-24">
          {/* Step 1 */}
          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
            <div>
              <div className="text-emerald-400 text-sm font-semibold mb-2">
                Step 1
              </div>
              <h3 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold">
                Add the pixel
              </h3>
              <p className="mt-3 text-zinc-400 leading-relaxed">
                One line of code in your site header. Takes 2 minutes. Works
                with any website — WordPress, Webflow, Squarespace, custom,
                whatever.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 overflow-x-auto">
              <pre className="text-xs sm:text-sm text-emerald-400 font-mono whitespace-pre">
                {`<script
  src="https://cdn.epi.lucflynn.com/p.js"
  data-site-id="site_abc123"
  async
></script>`}
              </pre>
            </div>
          </div>

          {/* Step 2 */}
          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
            <div className="md:order-2">
              <div className="text-emerald-400 text-sm font-semibold mb-2">
                Step 2
              </div>
              <h3 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold">
                Leads get scored automatically
              </h3>
              <p className="mt-3 text-zinc-400 leading-relaxed">
                Every form submission runs through 7 checks: email validation,
                phone intelligence, bot detection, IP analysis, duplicate
                detection, form timing, and ad attribution. Each lead gets a
                score from 0-100. You see exactly why.
              </p>
            </div>
            <div className="md:order-1">
              <MockBrowser>
                <MockLeadFeed />
              </MockBrowser>
            </div>
          </div>

          {/* Step 3 */}
          <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-center">
            <div>
              <div className="text-emerald-400 text-sm font-semibold mb-2">
                Step 3
              </div>
              <h3 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold">
                Get scores where you work
              </h3>
              <p className="mt-3 text-zinc-400 leading-relaxed">
                Dashboard. Slack. Email. Your sales team knows which leads to
                call first and which ones to skip.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 sm:p-6 space-y-3">
              <div className="flex items-center gap-3 rounded-lg bg-[#1a1d21] p-3 border border-zinc-700/50">
                <div className="w-8 h-8 rounded bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs font-bold shrink-0">
                  EPI
                </div>
                <div className="text-sm">
                  <p className="text-zinc-300">
                    <span className="font-semibold text-white">
                      New lead scored:
                    </span>{" "}
                    sarah.c@acmecorp.com
                  </p>
                  <p className="text-zinc-500 text-xs mt-0.5">
                    Score:{" "}
                    <span className="text-green-400 font-medium">
                      91 verified
                    </span>{" "}
                    {"\u00B7"} Google Ads {"\u00B7"} valid email {"\u00B7"}{" "}
                    mobile phone
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg bg-[#1a1d21] p-3 border border-zinc-700/50">
                <div className="w-8 h-8 rounded bg-red-500/20 flex items-center justify-center text-red-400 text-xs font-bold shrink-0">
                  EPI
                </div>
                <div className="text-sm">
                  <p className="text-zinc-300">
                    <span className="font-semibold text-white">
                      New lead scored:
                    </span>{" "}
                    info@tempmail.xyz
                  </p>
                  <p className="text-zinc-500 text-xs mt-0.5">
                    Score:{" "}
                    <span className="text-red-400 font-medium">8 junk</span>{" "}
                    {"\u00B7"} bot {"\u00B7"} disposable email {"\u00B7"}{" "}
                    datacenter IP
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TheScore() {
  const signals = [
    "Email validation — real address or disposable trash?",
    "Phone intelligence — mobile, landline, VOIP, or invalid?",
    "Bot detection — honeypot fields and form fill timing",
    "IP intelligence — VPN, proxy, datacenter, or residential?",
    "Duplicate detection — same person submitting multiple times?",
    "Form timing — filled in 0.5 seconds? That\u2019s a bot.",
    "Ad attribution — gclid, fbclid, UTM tracking verified",
  ];

  return (
    <section className="py-20 sm:py-28 border-t border-zinc-800/50">
      <div className="max-w-5xl mx-auto px-5 sm:px-6">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-center">
          Every score shows its math
        </h2>

        <div className="mt-12 sm:mt-16 max-w-2xl mx-auto">
          <MockBrowser>
            <MockMixedScoreBreakdown />
          </MockBrowser>
        </div>

        <div className="mt-12 sm:mt-16 max-w-2xl mx-auto">
          <div className="space-y-4 text-base sm:text-lg text-zinc-400 leading-relaxed">
            <p className="text-white font-semibold text-lg sm:text-xl">
              No black box. No {"\u201C"}trust our AI.{"\u201D"}
            </p>
            <p>
              Every lead starts at 50. Each signal moves the score up or down.
              You see every check, every point, every calculation.
            </p>
            <p>
              If we flag a lead as junk, you can see exactly why. If we say it
              {"'"}s verified, you can see the evidence.
            </p>
            <p className="text-white font-medium">
              The score is deterministic. Same inputs, same score. Every time.
            </p>
          </div>

          <div className="mt-10 space-y-3">
            {signals.map((signal, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-emerald-400 mt-0.5 shrink-0">
                  {"\u2713"}
                </span>
                <span className="text-zinc-300 text-sm sm:text-base">
                  {signal}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section
      id="pricing"
      className="py-20 sm:py-28 border-t border-zinc-800/50"
    >
      <div className="max-w-5xl mx-auto px-5 sm:px-6">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-center">
          Free to start. Pay when it{"'"}s working.
        </h2>

        <div className="mt-12 sm:mt-16 max-w-md mx-auto">
          <div className="rounded-2xl border border-zinc-700 bg-zinc-900/80 p-8 sm:p-10 text-center">
            <h3 className="font-[family-name:var(--font-display)] text-xl sm:text-2xl font-bold">
              EPI Lead Scoring
            </h3>
            <div className="mt-6 space-y-2 text-zinc-400">
              <p className="text-white font-semibold text-lg">
                First 100 leads scored free.
              </p>
              <p>No credit card required.</p>
            </div>
            <div className="mt-6 pt-6 border-t border-zinc-700/50 space-y-2 text-zinc-400">
              <p>
                After that:{" "}
                <span className="text-white font-semibold">$49/month</span>
              </p>
              <p>Unlimited leads. All 7 checks.</p>
              <p>Dashboard + Slack + Email delivery.</p>
            </div>
            <Link
              href="/sign-up"
              className="mt-8 inline-flex items-center justify-center w-full rounded-lg bg-emerald-500 px-6 py-3.5 text-base font-semibold text-white hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20"
            >
              Start scoring free
            </Link>
          </div>
          <p className="mt-6 text-center text-sm text-zinc-500">
            No contracts. Cancel anytime. Your data exports with you.
          </p>
        </div>
      </div>
    </section>
  );
}

function WhoItsFor() {
  const bullets = [
    "Reported a CPL that didn\u2019t match what the client actually saw in their CRM",
    'Had a client say "the leads are garbage" when your dashboard says they\u2019re great',
    'Wondered how many of your "conversions" are bots, duplicates, or junk',
    "Lost a client because they didn\u2019t trust the lead quality",
  ];

  return (
    <section className="py-20 sm:py-28 border-t border-zinc-800/50">
      <div className="max-w-3xl mx-auto px-5 sm:px-6">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight text-center">
          Built for media buyers and agencies
        </h2>
        <div className="mt-10 sm:mt-12">
          <p className="text-zinc-400 text-base sm:text-lg leading-relaxed">
            If you manage ad accounts for clients and you{"'"}ve ever:
          </p>
          <div className="mt-6 space-y-4">
            {bullets.map((bullet, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-zinc-500 mt-0.5 shrink-0">
                  {"\u2192"}
                </span>
                <span className="text-zinc-300 text-sm sm:text-base leading-relaxed">
                  {bullet}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-8 text-zinc-300 text-base sm:text-lg leading-relaxed">
            EPI shows you — and your client — exactly what{"'"}s real and what
            {"'"}s not. Install it on your client{"'"}s site. Share the
            dashboard. Let the data speak.
          </p>
        </div>
      </div>
    </section>
  );
}

function ClosingCTA() {
  return (
    <section className="py-20 sm:py-28 border-t border-zinc-800/50">
      <div className="max-w-3xl mx-auto px-5 sm:px-6 text-center">
        <h2 className="font-[family-name:var(--font-display)] text-2xl sm:text-3xl md:text-4xl font-bold tracking-tight">
          Stop guessing. Start scoring.
        </h2>
        <p className="mt-4 sm:mt-6 text-zinc-400 text-base sm:text-lg">
          100 leads scored free. Install in 5 minutes. See your first score
          breakdown today.
        </p>
        <Link
          href="/sign-up"
          className="mt-8 inline-flex items-center justify-center rounded-lg bg-emerald-500 px-8 py-4 text-lg font-semibold text-white hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20"
        >
          Start scoring free {"\u2192"}
        </Link>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-zinc-800/50 py-10 sm:py-12">
      <div className="max-w-5xl mx-auto px-5 sm:px-6 text-center">
        <p className="text-sm text-zinc-500">
          EPI by Stygies VIII
        </p>
        <p className="mt-1 text-sm text-zinc-600">
          Built in Albuquerque, NM by a media buyer tired of fake leads.
        </p>
      </div>
    </footer>
  );
}

// ── Sticky Mobile CTA ──

function StickyMobileCTA() {
  return (
    <div className="fixed bottom-0 inset-x-0 p-3 bg-[#09090b]/90 backdrop-blur-sm border-t border-zinc-800 lg:hidden z-50">
      <Link
        href="/sign-up"
        className="flex items-center justify-center w-full rounded-lg bg-emerald-500 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-400 transition shadow-lg shadow-emerald-500/20"
      >
        Start scoring free — 100 leads on us
      </Link>
    </div>
  );
}

// ── Page ──

export default function LandingPage() {
  return (
    <>
      <Hero />
      <Problem />
      <HowItWorks />
      <TheScore />
      <Pricing />
      <WhoItsFor />
      <ClosingCTA />
      <Footer />
      <StickyMobileCTA />
      {/* Spacer for sticky CTA on mobile */}
      <div className="h-16 lg:hidden" />
    </>
  );
}
