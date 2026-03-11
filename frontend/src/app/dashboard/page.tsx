"use client";

import { useEffect, useState, useCallback } from "react";
import { UserButton } from "@clerk/nextjs";
import { useApi } from "@/lib/use-api";
import type { Site, Lead, UserInfo, ScoringSignal, PixelStatus, GoogleAdsConnection, MetaAdsConnection, SlackConnection, PaginatedLeads, CampaignPerformance, LeadStats } from "@/lib/api";

type Tab = "leads" | "setup" | "usage" | "google_ads";

// ── Helpers ──

// Reconstruct scoring signals from individual lead fields when scoring_signals blob is missing
function reconstructSignals(lead: Lead): ScoringSignal[] {
  const signals: ScoringSignal[] = [];
  if (lead.is_bot) signals.push({ signal: "bot_detected", points: -40, detail: "Automated submission detected" });
  if (lead.honeypot_triggered) signals.push({ signal: "honeypot_triggered", points: -30, detail: "Hidden field was filled" });
  if (lead.is_duplicate) signals.push({ signal: "duplicate", points: -20, detail: "Same contact submitted within 24h" });
  if (lead.email_valid === "valid") signals.push({ signal: "valid_email", points: 20, detail: "Deliverable, not disposable" });
  else if (lead.email_valid === "catch_all") signals.push({ signal: "catch_all_email", points: 5, detail: "Catch-all domain" });
  else if (lead.email_valid === "disposable") signals.push({ signal: "disposable_email", points: -15, detail: "Disposable/temporary email" });
  else if (lead.email_valid === "invalid") signals.push({ signal: "invalid_email", points: -25, detail: "Email is undeliverable" });
  if (lead.phone_valid === "valid" || lead.phone_valid === "mobile") signals.push({ signal: "valid_phone", points: 15, detail: `Valid ${lead.phone_valid} number` });
  else if (lead.phone_valid === "landline") signals.push({ signal: "landline_phone", points: 5, detail: "Valid landline number" });
  else if (lead.phone_valid === "voip") signals.push({ signal: "voip_phone", points: -5, detail: "VOIP number" });
  else if (lead.phone_valid === "invalid") signals.push({ signal: "invalid_phone", points: -15, detail: "Phone number is invalid" });
  if (lead.gclid) signals.push({ signal: "gclid_present", points: 10, detail: "Google Ads click ID detected" });
  else if (lead.fbclid) signals.push({ signal: "fbclid_present", points: 10, detail: "Meta Ads click ID detected" });
  if (lead.form_fill_time_ms && lead.form_fill_time_ms > 3000) signals.push({ signal: "human_timing", points: 5, detail: `Form filled in ${(lead.form_fill_time_ms / 1000).toFixed(1)}s` });
  return signals;
}

function getEffectiveSignals(lead: Lead): ScoringSignal[] {
  return lead.scoring_signals?.signals_fired ?? reconstructSignals(lead);
}

function ClickIdBadge({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="text-green-600">✓</span> {label}
      <button
        onClick={(e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(value);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        }}
        className="text-gray-400 hover:text-gray-600"
      >
        {copied ? "copied" : "copy"}
      </button>
    </span>
  );
}

function humanAttribution(tier: string, gclid?: string | null, fbclid?: string | null): string {
  if (tier === "definitive") {
    if (gclid) return "Tracked from Google Ads click";
    if (fbclid) return "Tracked from Meta Ads click";
    return "Tracked from ad click";
  }
  if (tier === "high_confidence") return "Ad platform UTM match";
  if (tier === "probable") return "Has UTM or referrer signal";
  return "No attribution signal";
}

const LABEL_COLORS: Record<string, string> = {
  verified: "bg-green-100 text-green-700",
  likely_real: "bg-lime-100 text-lime-700",
  suspicious: "bg-orange-100 text-orange-700",
  junk: "bg-red-100 text-red-700",
  paused: "bg-gray-100 text-gray-500",
};

function ScoreBadge({ score, label }: { score?: number; label?: string }) {
  const color = LABEL_COLORS[label || ""] || "bg-gray-100 text-gray-500";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}>
      {score != null && <span>{score}</span>}
      {label && <span>{label.replace("_", " ")}</span>}
    </span>
  );
}

function getFlags(lead: Lead): string[] {
  const flags: string[] = [];
  if (lead.is_duplicate) flags.push("duplicate");
  if (lead.is_bot) flags.push("bot");
  if (lead.email_valid === "disposable") flags.push("disposable email");
  if (lead.email_valid === "invalid") flags.push("invalid email");
  if (lead.phone_valid === "voip") flags.push("voip phone");
  if (lead.phone_valid === "invalid") flags.push("invalid phone");
  if (lead.honeypot_triggered) flags.push("honeypot");
  if (lead.scoring_signals?.checks?.ip?.vpn) flags.push("VPN");
  if (lead.scoring_signals?.checks?.ip?.datacenter) flags.push("datacenter IP");
  return flags;
}

// ── Pixel Status Bar ──

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

const STATUS_STYLES = {
  active: { dot: "bg-green-500", text: "text-green-700", bg: "border-l-green-500", label: "Pixel active" },
  idle: { dot: "bg-amber-400", text: "text-amber-700", bg: "border-l-amber-400", label: "Pixel idle" },
  inactive: { dot: "bg-red-500", text: "text-red-700", bg: "border-l-red-500", label: "No events received" },
  waiting: { dot: "bg-gray-400 animate-pulse", text: "text-gray-500", bg: "border-l-gray-400", label: "Waiting for first event..." },
} as const;

function PixelStatusBar({ sites, statuses }: { sites: Site[]; statuses: Record<string, PixelStatus> }) {
  const [, setTick] = useState(0);

  // Re-render every 30s to keep relative time fresh
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(interval);
  }, []);

  const entries = sites.filter((site) => statuses[site.id]);
  if (entries.length === 0) return null;

  return (
    <div className="divide-y divide-gray-100">
      {entries.map((site) => {
        const status = statuses[site.id];
        const s = STATUS_STYLES[status.pixel_status];
        return (
          <div key={site.id} className={`flex items-center gap-2 px-4 py-2 text-sm border-l-4 ${s.bg} bg-gray-50`}>
            <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${s.dot}`} />
            <span className="font-medium text-gray-700 truncate">{site.name || site.domain}</span>
            <span className={`${s.text} shrink-0`}>{s.label.toLowerCase()}</span>
            {status.last_event_at && (
              <span className="text-gray-500 shrink-0">
                · {relativeTime(status.last_event_at)}
              </span>
            )}
            {status.page_views_today > 0 && (
              <span className="text-gray-500 shrink-0">
                · {status.page_views_today} view{status.page_views_today === 1 ? "" : "s"} today
              </span>
            )}
            {status.pixel_status === "waiting" && (
              <span className="text-gray-400 shrink-0">· listening</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Shared Detail Row ──

type RowStatus = "good" | "bad" | "neutral";

function DetailRow({
  status,
  label,
  value,
  points,
  running,
}: {
  status?: RowStatus;
  label: string;
  value?: string;
  points?: number;
  running?: number;
}) {
  const iconColor = status === "good" ? "text-green-600" : status === "bad" ? "text-red-500" : "text-transparent";
  const icon = status === "good" ? "✓" : status === "bad" ? "✗" : " ";
  const valueColor =
    status === "good" ? "text-green-600" : status === "bad" ? "text-red-500" : "text-gray-400";

  return (
    <div className="flex items-center justify-between text-sm py-1.5 border-b border-gray-100 px-2">
      <div className="flex items-center gap-2 min-w-0">
        <span className={`w-3.5 shrink-0 text-center ${iconColor}`}>{icon}</span>
        <span className="text-gray-700">{label}</span>
      </div>
      <div className="flex items-center gap-3 shrink-0 ml-4">
        {value && <span className={`text-sm ${valueColor}`}>{value}</span>}
        {points != null && (
          <span className={`font-mono text-xs w-10 text-right ${points > 0 ? "text-green-600" : "text-red-500"}`}>
            {points > 0 ? "+" : ""}{points}
          </span>
        )}
        {running != null && (
          <span className="text-gray-400 text-xs w-10 text-right font-mono">→ {running}</span>
        )}
      </div>
    </div>
  );
}

// ── Lead Detail Panel ──

function LeadDetail({ lead, onClose }: { lead: Lead; onClose: () => void }) {
  const ss = lead.scoring_signals;
  const checks = ss?.checks;
  const signals = getEffectiveSignals(lead);

  const tier = checks?.attribution?.tier || lead.attribution_tier || "unattributed";
  const gclidVal = checks?.attribution?.gclid || lead.gclid;
  const fbclidVal = checks?.attribution?.fbclid || lead.fbclid;
  const formFillMs = checks?.bot?.form_fill_ms ?? lead.form_fill_time_ms;
  const honeypot = checks?.bot?.honeypot ?? lead.honeypot_triggered;

  // Resolve check values
  const emailStatus = checks?.email?.status || lead.email_valid;
  const phoneStatus = checks?.phone?.status || lead.phone_valid;
  const isDup = ss?.dedup?.is_duplicate || lead.is_duplicate;

  // Build "What We Found" rows — only include checks that were actually performed
  const checkRows: { status?: RowStatus; label: string; value: string }[] = [];

  // Identity
  if (lead.email || checks?.email?.provided) {
    const good = emailStatus === "valid";
    const bad = emailStatus === "disposable" || emailStatus === "invalid";
    checkRows.push({
      status: good ? "good" : bad ? "bad" : "neutral",
      label: "Email",
      value: emailStatus || "unknown",
    });
  }
  if (lead.phone || checks?.phone?.provided) {
    const good = phoneStatus === "valid" || phoneStatus === "mobile";
    const bad = phoneStatus === "invalid";
    checkRows.push({
      status: good ? "good" : bad ? "bad" : "neutral",
      label: "Phone",
      value: `${lead.phone || "(provided)"} · ${phoneStatus || "unknown"}`,
    });
  }
  if (isDup) {
    const dupDetail = ss?.dedup?.count ? `${ss.dedup.count}x` : "yes";
    const firstSeen = ss?.dedup?.first_seen ? ` · first seen ${new Date(ss.dedup.first_seen).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}` : "";
    checkRows.push({ status: "bad", label: "Duplicate", value: `${dupDetail}${firstSeen}` });
  }

  // Bot detection
  if (honeypot != null || checks?.bot) {
    checkRows.push({
      status: honeypot ? "bad" : "good",
      label: "Honeypot",
      value: honeypot ? "triggered" : "clean",
    });
  }
  if (formFillMs != null) {
    const fast = formFillMs < 800;
    checkRows.push({
      status: fast ? "bad" : "good",
      label: "Form fill time",
      value: fast ? `${(formFillMs / 1000).toFixed(1)}s · too fast` : `${(formFillMs / 1000).toFixed(1)}s`,
    });
  }
  if (checks?.bot?.user_agent_bot) {
    checkRows.push({ status: "bad", label: "User agent", value: "bot detected" });
  }

  // Network
  if (checks?.ip) {
    const isDatacenter = checks.ip.datacenter;
    const isVpnProxy = checks.ip.vpn || checks.ip.proxy;
    checkRows.push({
      status: isDatacenter ? "bad" : "neutral",
      label: "IP",
      value: isDatacenter ? "datacenter" : "residential",
    });
    checkRows.push({
      status: isVpnProxy ? "bad" : "good",
      label: "VPN/Proxy",
      value: isVpnProxy ? "yes" : "no",
    });
    if (checks.ip.country) {
      checkRows.push({ status: "neutral", label: "Country", value: checks.ip.country });
    }
  }

  // Attribution
  const attrValue = tier === "definitive"
    ? (gclidVal ? "Google Ads click" : fbclidVal ? "Meta Ads click" : "ad click")
    : tier === "high_confidence" ? "UTM match"
    : tier === "probable" ? "UTM/referrer signal"
    : "none";
  checkRows.push({ status: "neutral", label: "Attribution", value: attrValue });

  return (
    <div className="border-t border-gray-200 bg-gray-50 px-4 py-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-base font-semibold text-gray-900">
            {lead.email || lead.phone || lead.name || "Unknown contact"}
          </p>
          <p className="text-sm text-gray-500 mt-0.5">
            Score: {lead.quality_score} — <span className="uppercase">{lead.quality_label?.replace("_", " ")}</span>
            {" · "}{new Date(lead.created_at).toLocaleString()}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
      </div>

      {/* Section 1: What We Found */}
      {checkRows.length > 0 && (
        <div className="mb-1">
          <p className="text-xs text-gray-400 mb-1.5">What We Found</p>
          {checkRows.map((row, i) => (
            <DetailRow key={i} status={row.status} label={row.label} value={row.value} />
          ))}
        </div>
      )}

      {/* Section 2: Score */}
      {signals.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-1.5 mt-3">Score</p>
          <div className="flex items-center justify-between text-sm text-gray-400 py-1.5 border-b border-gray-200 bg-gray-100/50 px-2 rounded-t">
            <div className="flex items-center gap-2">
              <span className="w-3.5" />
              <span>Baseline</span>
            </div>
            <span className="font-mono text-xs w-10 text-right">50</span>
          </div>
          {(() => {
            let running = 50;
            return signals.map((s, i) => {
              running = Math.max(0, Math.min(100, running + s.points));
              return (
                <DetailRow
                  key={i}
                  status={s.points > 0 ? "good" : "bad"}
                  label={s.detail || s.signal.replace(/_/g, " ")}
                  points={s.points}
                  running={running}
                />
              );
            });
          })()}
          <div className="flex items-center justify-between text-sm font-semibold text-gray-900 py-1.5 bg-gray-100/50 px-2 rounded-b">
            <div className="flex items-center gap-2">
              <span className="w-3.5" />
              <span>Final</span>
            </div>
            <span className="font-mono text-xs w-10 text-right">{lead.quality_score}</span>
          </div>
        </div>
      )}

      {/* Attribution details — click IDs, UTM, referrer */}
      {(gclidVal || fbclidVal || lead.utm_source || lead.utm_campaign || checks?.attribution?.referrer) && (
        <div className="mt-3 text-xs text-gray-400 space-y-0.5 px-2">
          {gclidVal && <p><ClickIdBadge label="Google click ID" value={gclidVal} /></p>}
          {fbclidVal && <p><ClickIdBadge label="Meta click ID" value={fbclidVal} /></p>}
          {(() => {
            const src = checks?.attribution?.utm_source || lead.utm_source;
            const med = checks?.attribution?.utm_medium || lead.utm_medium;
            if (src || med) return <p className="text-gray-500">{src && `Source: ${src}`}{src && med && " · "}{med && `Medium: ${med}`}</p>;
            return null;
          })()}
          {(checks?.attribution?.utm_campaign || lead.utm_campaign) && (
            <p className="text-gray-500">Campaign: {checks?.attribution?.utm_campaign || lead.utm_campaign}</p>
          )}
          {checks?.attribution?.referrer && <p className="text-gray-500">Referrer: {checks.attribution.referrer}</p>}
        </div>
      )}
    </div>
  );
}

// ── Stats Bar ──

function StatsBar({ stats }: { stats: LeadStats | null }) {
  if (!stats) return null;

  return (
    <div className="flex items-center gap-3 px-4 py-2 text-xs text-gray-500 border-b border-gray-100 flex-wrap">
      <span>Total: <strong className="text-gray-700">{stats.total_leads}</strong></span>
      <span className="text-green-600">Verified: {stats.verified}</span>
      <span className="text-lime-600">Likely Real: {stats.likely_real}</span>
      <span className="text-orange-600">Suspicious: {stats.suspicious}</span>
      <span className="text-red-600">Junk: {stats.junk}</span>
    </div>
  );
}

// ── Scoring Help Modal ──

function ScoringHelp({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">How EPI Scores Leads</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
        </div>
        <div className="text-sm text-gray-600 space-y-3">
          <p>Every lead starts at <strong>50</strong> and gets adjusted based on what we find.</p>
          <p className="font-semibold text-gray-900">We check:</p>
          <ul className="space-y-1 ml-4 list-disc">
            <li><strong>Email</strong> — Is it a real, deliverable email? Or disposable/invalid?</li>
            <li><strong>Phone</strong> — Is it a real number? Mobile, landline, or VOIP?</li>
            <li><strong>Duplicates</strong> — Has this person submitted before recently?</li>
            <li><strong>Bot detection</strong> — Did a human fill out this form or a bot?</li>
            <li><strong>Network</strong> — Is the submission from a VPN, proxy, or datacenter?</li>
            <li><strong>Attribution</strong> — Can we trace this lead back to a specific ad click?</li>
          </ul>
          <p className="font-semibold text-gray-900">Score ranges:</p>
          <div className="space-y-1">
            <p><span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-2" />75+ <strong>Verified</strong> — Strong signals this is a real person from a real ad click</p>
            <p><span className="inline-block w-3 h-3 rounded-full bg-lime-500 mr-2" />50-74 <strong>Likely Real</strong> — Looks legitimate but missing some verification signals</p>
            <p><span className="inline-block w-3 h-3 rounded-full bg-orange-400 mr-2" />25-49 <strong>Suspicious</strong> — Multiple warning flags, review before pursuing</p>
            <p><span className="inline-block w-3 h-3 rounded-full bg-red-500 mr-2" />0-24 <strong>Junk</strong> — Very likely bot, fake, or spam</p>
          </div>
          <p className="text-gray-900 font-medium italic mt-4">
            No black box. No AI vibes. Just signal checks and math.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Lead Feed ──

function LeadFeed({
  leads,
  userInfo,
  sites,
  totalLeads,
  onLoadMore,
  loadingMore,
  stats,
}: {
  leads: Lead[];
  userInfo: UserInfo | null;
  sites: Site[];
  totalLeads: number;
  onLoadMore: () => void;
  loadingMore: boolean;
  stats: LeadStats | null;
}) {
  const siteMap = Object.fromEntries(sites.map((s) => [s.id, s]));
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const hasMore = leads.length < totalLeads;

  if (leads.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No leads yet. Once someone submits a form on your site, scores will appear here.
      </div>
    );
  }

  return (
    <div>
      {/* Lead count + stats bar */}
      <div className="flex items-center justify-between px-4 py-2 text-xs text-gray-500 border-b border-gray-100">
        <span>Showing <strong className="text-gray-700">{leads.length}</strong> of <strong className="text-gray-700">{totalLeads}</strong> leads</span>
      </div>
      <StatsBar stats={stats} />

      {/* Usage indicator */}
      {userInfo && userInfo.plan === "free" && (
        <div className="bg-blue-50 px-4 py-2 text-xs text-blue-700 border-b border-blue-100">
          {userInfo.usage_count} of {userInfo.usage_limit} free leads scored
        </div>
      )}

      {/* Help link */}
      <div className="px-4 py-1.5 border-b border-gray-100 text-right">
        <button onClick={() => setShowHelp(true)} className="text-xs text-blue-500 hover:text-blue-700">
          How scoring works (?)
        </button>
      </div>

      {showHelp && <ScoringHelp onClose={() => setShowHelp(false)} />}

      {/* Lead rows */}
      <div className="divide-y divide-gray-100">
        {leads.map((lead) => {
          const flags = getFlags(lead);
          const isExpanded = expandedId === lead.id;
          return (
            <div key={lead.id}>
              <div
                className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 transition"
                onClick={() => setExpandedId(isExpanded ? null : lead.id)}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <ScoreBadge score={lead.quality_score} label={lead.quality_label} />
                    {lead.email && (
                      <span className="truncate text-sm font-medium text-gray-900">{lead.email}</span>
                    )}
                    {!lead.email && lead.phone && (
                      <span className="truncate text-sm font-medium text-gray-900">{lead.phone}</span>
                    )}
                    {!lead.email && !lead.phone && (
                      <span className="text-sm text-gray-400">No contact info</span>
                    )}
                  </div>
                  <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-400">
                    {siteMap[lead.site_id] && (
                      <span className="text-gray-500 font-medium">{siteMap[lead.site_id].name || siteMap[lead.site_id].domain}</span>
                    )}
                    <span>{new Date(lead.created_at).toLocaleString()}</span>
                  </div>
                  {/* Flags line — only for sub-75 scores */}
                  {flags.length > 0 && (lead.quality_score == null || lead.quality_score < 75) && (
                    <div className="mt-0.5 text-xs text-orange-600">
                      Flags: {flags.join(" · ")}
                    </div>
                  )}
                  {/* Attribution line */}
                  <div className="mt-0.5 text-xs text-gray-400">
                    {lead.gclid ? (
                      <span>Google Ads{lead.utm_campaign ? ` · Campaign: ${lead.utm_campaign}` : ""}{` · Source: ${lead.utm_source || "google"} / ${lead.utm_medium || "cpc"}`}</span>
                    ) : lead.utm_source ? (
                      <span>{lead.utm_source} / {lead.utm_medium || "unknown"}{lead.utm_campaign ? ` · Campaign: ${lead.utm_campaign}` : ""}</span>
                    ) : (
                      <span>Direct / No attribution</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-2">
                  {lead.attribution_tier && lead.attribution_tier !== "unattributed" && (
                    <span className="rounded bg-purple-50 px-2 py-0.5 text-xs text-purple-600">
                      {lead.attribution_tier}
                    </span>
                  )}
                  {lead.is_duplicate && (
                    <span className="rounded bg-orange-50 px-2 py-0.5 text-xs text-orange-600">dup</span>
                  )}
                  <span className="text-gray-300 text-xs">{isExpanded ? "▲" : "▼"}</span>
                </div>
              </div>
              {isExpanded && <LeadDetail lead={lead} onClose={() => setExpandedId(null)} />}
            </div>
          );
        })}
      </div>

      {/* Load more */}
      {hasMore && (
        <div className="px-4 py-4 text-center border-t border-gray-100">
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            className="rounded-lg bg-gray-100 px-6 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50"
          >
            {loadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Setup Panel ──

function McpPanel({ getApi }: { getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>> }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const api = await getApi();
      const { api_key } = await api.generateApiKey();
      setApiKey(api_key);
    } finally {
      setGenerating(false);
    }
  };

  const mcpConfig = apiKey
    ? JSON.stringify(
        {
          mcpServers: {
            epi: {
              command: "npx",
              args: ["-y", "epi-mcp-server"],
              env: { EPI_API_KEY: apiKey },
            },
          },
        },
        null,
        2
      )
    : null;

  const copyConfig = () => {
    if (mcpConfig) {
      navigator.clipboard.writeText(mcpConfig);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-gray-900">MCP Server</h3>
        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-600 font-medium">
          Claude &middot; Cursor &middot; Windsurf
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-3">
        Query your leads directly from AI tools. Generate an API key, then add the config to your MCP client.
      </p>
      {!apiKey ? (
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate API Key"}
        </button>
      ) : (
        <div className="space-y-3">
          <div>
            <p className="text-xs text-gray-400 mb-1">Your API Key (save this — it won{"'"}t be shown again)</p>
            <code className="block rounded bg-gray-100 px-3 py-2 text-xs font-mono text-gray-700 break-all select-all">
              {apiKey}
            </code>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Add to your Claude / Cursor config</p>
            <div className="relative">
              <pre className="overflow-x-auto rounded bg-gray-900 p-3 text-xs text-green-400 font-mono">
                {mcpConfig}
              </pre>
              <button
                onClick={copyConfig}
                className="absolute top-1.5 right-1.5 rounded bg-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-600"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Account Selector Modal ──

function AccountSelectorModal({
  title,
  accounts,
  idKey,
  nameKey,
  onSelect,
  onCancel,
}: {
  title: string;
  accounts: Record<string, string>[];
  idKey: string;
  nameKey: string;
  onSelect: (id: string, name: string) => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onCancel}>
      <div className="bg-white rounded-xl max-w-md w-full p-6 max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 text-xl">x</button>
        </div>
        <p className="text-sm text-gray-500 mb-4">You have access to multiple accounts. Select the one to connect:</p>
        <div className="space-y-2">
          {accounts.map((acct) => (
            <button
              key={acct[idKey]}
              onClick={() => onSelect(acct[idKey], acct[nameKey] || acct[idKey])}
              className="w-full text-left rounded-lg border border-gray-200 px-4 py-3 hover:border-blue-400 hover:bg-blue-50 transition"
            >
              <p className="text-sm font-medium text-gray-900">{acct[nameKey] || "Unnamed"}</p>
              <p className="text-xs text-gray-400">{acct[idKey]}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function GoogleAdsPanel({
  getApi,
}: {
  getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>>;
}) {
  const [connections, setConnections] = useState<GoogleAdsConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [pendingAccounts, setPendingAccounts] = useState<{ connectionId: string; accounts: Record<string, string>[] } | null>(null);

  const fetchConnections = useCallback(async () => {
    try {
      const api = await getApi();
      const conns = await api.getGoogleAdsConnections();
      setConnections(conns);
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, [getApi]);

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const googleAds = params.get("google_ads");
    if (googleAds === "connected") {
      setMessage({ type: "success", text: "Google Ads account connected successfully!" });
      window.history.replaceState({}, "", window.location.pathname);
      fetchConnections();
    } else if (googleAds === "select") {
      const connectionId = params.get("connection_id");
      if (connectionId) {
        window.history.replaceState({}, "", window.location.pathname);
        (async () => {
          try {
            const api = await getApi();
            const data = await api.getGoogleAdsPendingAccounts(connectionId);
            setPendingAccounts({ connectionId: data.connection_id, accounts: data.accounts as unknown as Record<string, string>[] });
          } catch {
            setMessage({ type: "error", text: "Failed to load accounts. Please try again." });
          }
        })();
      }
    } else if (googleAds === "error") {
      setMessage({ type: "error", text: "Failed to connect Google Ads account. Please try again." });
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [fetchConnections, getApi]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const api = await getApi();
      const { auth_url } = await api.getGoogleAdsAuthUrl();
      window.location.href = auth_url;
    } catch {
      setMessage({ type: "error", text: "Failed to start connection. Please try again." });
      setConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    try {
      const api = await getApi();
      await api.disconnectGoogleAds(connectionId);
      setMessage({ type: "success", text: "Google Ads account disconnected." });
      fetchConnections();
    } catch {
      setMessage({ type: "error", text: "Failed to disconnect. Please try again." });
    }
  };

  const handleSelectAccount = async (customerId: string, accountName: string) => {
    if (!pendingAccounts) return;
    try {
      const api = await getApi();
      await api.selectGoogleAdsAccount(pendingAccounts.connectionId, customerId, accountName);
      setPendingAccounts(null);
      setMessage({ type: "success", text: `Connected to ${accountName}` });
      fetchConnections();
    } catch {
      setMessage({ type: "error", text: "Failed to select account. Please try again." });
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-3 w-48 rounded bg-gray-100" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-gray-900">Google Ads</h3>
        {connections.length > 0 && (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-600 font-medium">
            Connected
          </span>
        )}
      </div>

      {message && (
        <div className={`mb-3 rounded-lg px-3 py-2 text-xs ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      {pendingAccounts && (
        <AccountSelectorModal
          title="Select Google Ads Account"
          accounts={pendingAccounts.accounts}
          idKey="customer_id"
          nameKey="descriptive_name"
          onSelect={handleSelectAccount}
          onCancel={() => setPendingAccounts(null)}
        />
      )}

      {connections.length === 0 ? (
        <>
          <p className="text-xs text-gray-500 mb-3">
            Connect your Google Ads account to pull campaign data, match conversions to leads, and enable attribution tracking.
          </p>
          <button onClick={handleConnect} disabled={connecting} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {connecting ? "Redirecting..." : "Connect Google Ads"}
          </button>
        </>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => (
            <div key={conn.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <div>
                <p className="text-sm font-medium text-gray-900">{conn.account_name || conn.customer_id}</p>
                <p className="text-xs text-gray-400">
                  {conn.customer_id}
                  {conn.connected_at && ` · connected ${new Date(conn.connected_at).toLocaleDateString()}`}
                </p>
              </div>
              <button onClick={() => handleDisconnect(conn.id)} className="rounded bg-gray-200 px-3 py-1 text-xs font-medium text-gray-600 hover:bg-red-100 hover:text-red-600">
                Disconnect
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MetaAdsPanel({
  getApi,
}: {
  getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>>;
}) {
  const [connections, setConnections] = useState<MetaAdsConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [pendingAccounts, setPendingAccounts] = useState<{ connectionId: string; accounts: Record<string, string>[] } | null>(null);

  const fetchConnections = useCallback(async () => {
    try {
      const api = await getApi();
      const conns = await api.getMetaAdsConnections();
      setConnections(conns);
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, [getApi]);

  useEffect(() => { fetchConnections(); }, [fetchConnections]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const metaAds = params.get("meta_ads");
    if (metaAds === "connected") {
      setMessage({ type: "success", text: "Meta Ads account connected successfully!" });
      window.history.replaceState({}, "", window.location.pathname);
      fetchConnections();
    } else if (metaAds === "select") {
      const connectionId = params.get("connection_id");
      if (connectionId) {
        window.history.replaceState({}, "", window.location.pathname);
        (async () => {
          try {
            const api = await getApi();
            const data = await api.getMetaAdsPendingAccounts(connectionId);
            setPendingAccounts({ connectionId: data.connection_id, accounts: data.accounts as unknown as Record<string, string>[] });
          } catch {
            setMessage({ type: "error", text: "Failed to load accounts. Please try again." });
          }
        })();
      }
    } else if (metaAds === "error") {
      setMessage({ type: "error", text: "Failed to connect Meta Ads account. Please try again." });
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [fetchConnections, getApi]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const api = await getApi();
      const { auth_url } = await api.getMetaAdsAuthUrl();
      window.location.href = auth_url;
    } catch {
      setMessage({ type: "error", text: "Failed to start connection. Please try again." });
      setConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    try {
      const api = await getApi();
      await api.disconnectMetaAds(connectionId);
      setMessage({ type: "success", text: "Meta Ads account disconnected." });
      fetchConnections();
    } catch {
      setMessage({ type: "error", text: "Failed to disconnect. Please try again." });
    }
  };

  const handleSelectAccount = async (accountId: string, accountName: string) => {
    if (!pendingAccounts) return;
    try {
      const api = await getApi();
      await api.selectMetaAdsAccount(pendingAccounts.connectionId, accountId, accountName);
      setPendingAccounts(null);
      setMessage({ type: "success", text: `Connected to ${accountName}` });
      fetchConnections();
    } catch {
      setMessage({ type: "error", text: "Failed to select account. Please try again." });
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-3 w-48 rounded bg-gray-100" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-gray-900">Meta Ads</h3>
        {connections.length > 0 && (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-600 font-medium">
            Connected
          </span>
        )}
      </div>
      {message && (
        <div className={`mb-3 rounded-lg px-3 py-2 text-xs ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}
      {pendingAccounts && (
        <AccountSelectorModal
          title="Select Meta Ad Account"
          accounts={pendingAccounts.accounts}
          idKey="account_id"
          nameKey="name"
          onSelect={handleSelectAccount}
          onCancel={() => setPendingAccounts(null)}
        />
      )}
      {connections.length === 0 ? (
        <>
          <p className="text-xs text-gray-500 mb-3">Connect your Meta Ads account to pull campaign data and enable attribution tracking.</p>
          <button onClick={handleConnect} disabled={connecting} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {connecting ? "Redirecting..." : "Connect Meta Ads"}
          </button>
        </>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => (
            <div key={conn.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <div>
                <p className="text-sm font-medium text-gray-900">{conn.account_name || conn.account_id || "Meta Ads"}</p>
                <p className="text-xs text-gray-400">
                  {conn.account_id && `${conn.account_id} · `}
                  {conn.connected_at && `connected ${new Date(conn.connected_at).toLocaleDateString()}`}
                </p>
              </div>
              <button onClick={() => handleDisconnect(conn.id)} className="rounded bg-gray-200 px-3 py-1 text-xs font-medium text-gray-600 hover:bg-red-100 hover:text-red-600">
                Disconnect
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SlackPanel({
  getApi,
}: {
  getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>>;
}) {
  const [connections, setConnections] = useState<SlackConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchConnections = useCallback(async () => {
    try {
      const api = await getApi();
      const conns = await api.getSlackConnections();
      setConnections(conns);
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, [getApi]);

  useEffect(() => { fetchConnections(); }, [fetchConnections]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const slack = params.get("slack");
    if (slack === "connected") {
      setMessage({ type: "success", text: "Slack workspace connected!" });
      window.history.replaceState({}, "", window.location.pathname);
      fetchConnections();
    } else if (slack === "error") {
      setMessage({ type: "error", text: "Failed to connect Slack. Please try again." });
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [fetchConnections]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const api = await getApi();
      const { install_url } = await api.getSlackInstallUrl();
      window.location.href = install_url;
    } catch {
      setMessage({ type: "error", text: "Failed to start connection. Please try again." });
      setConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    try {
      const api = await getApi();
      await api.disconnectSlack(connectionId);
      setMessage({ type: "success", text: "Slack workspace disconnected." });
      fetchConnections();
    } catch {
      setMessage({ type: "error", text: "Failed to disconnect. Please try again." });
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-3 w-48 rounded bg-gray-100" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-sm font-semibold text-gray-900">Slack</h3>
        {connections.length > 0 && (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-600 font-medium">
            Connected
          </span>
        )}
      </div>
      {message && (
        <div className={`mb-3 rounded-lg px-3 py-2 text-xs ${message.type === "success" ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}
      {connections.length === 0 ? (
        <>
          <p className="text-xs text-gray-500 mb-3">Connect Slack to get lead notifications in your workspace.</p>
          <button onClick={handleConnect} disabled={connecting} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {connecting ? "Redirecting..." : "Add to Slack"}
          </button>
        </>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => (
            <div key={conn.id} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <div>
                <p className="text-sm font-medium text-gray-900">{conn.workspace_name || "Slack Workspace"}</p>
                <p className="text-xs text-gray-400">
                  {conn.channel_name && `#${conn.channel_name} · `}
                  {conn.connected_at && `connected ${new Date(conn.connected_at).toLocaleDateString()}`}
                </p>
              </div>
              <button onClick={() => handleDisconnect(conn.id)} className="rounded bg-gray-200 px-3 py-1 text-xs font-medium text-gray-600 hover:bg-red-100 hover:text-red-600">
                Disconnect
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SetupPanel({
  sites,
  onAddSite,
  pixelStatuses,
  getApi,
}: {
  sites: Site[];
  onAddSite: (domain: string, name: string) => Promise<void>;
  pixelStatuses: Record<string, PixelStatus>;
  getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>>;
}) {
  const [domain, setDomain] = useState("");
  const [name, setName] = useState("");
  const [adding, setAdding] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const handleAdd = async () => {
    setAdding(true);
    try {
      await onAddSite(domain, name);
      setDomain("");
      setName("");
      setShowForm(false);
    } finally {
      setAdding(false);
    }
  };

  const copySnippet = (snippet: string, id: string) => {
    navigator.clipboard.writeText(snippet);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-6 p-4">
      {sites.map((site) => (
        <div key={site.id} className="rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">{site.name}</h3>
              <p className="text-xs text-gray-400">{site.domain}</p>
            </div>
            {(() => {
              const ps = pixelStatuses[site.id]?.pixel_status;
              const dotColor = ps === "active" ? "bg-green-500" : ps === "idle" ? "bg-amber-400" : ps === "inactive" ? "bg-red-500" : site.pixel_verified ? "bg-green-500" : "bg-gray-400 animate-pulse";
              const bgColor = ps === "active" ? "bg-green-100 text-green-700" : ps === "idle" ? "bg-amber-100 text-amber-700" : ps === "inactive" ? "bg-red-100 text-red-700" : site.pixel_verified ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500";
              const label = ps === "active" ? "Active" : ps === "idle" ? "Idle" : ps === "inactive" ? "Inactive" : site.pixel_verified ? "Active" : "Pending";
              return (
                <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${bgColor}`}>
                  <span className={`h-2 w-2 rounded-full ${dotColor}`} />
                  {label}
                </span>
              );
            })()}
          </div>
          {site.pixel_snippet && (
            <div className="mt-3">
              <div className="relative">
                <pre className="overflow-x-auto rounded bg-gray-900 p-3 text-xs text-green-400 font-mono">
                  {site.pixel_snippet}
                </pre>
                <button
                  onClick={() => copySnippet(site.pixel_snippet!, site.id)}
                  className="absolute top-1.5 right-1.5 rounded bg-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-600"
                >
                  {copied === site.id ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Google & Meta hidden until account selector is fixed */}
      {/* <GoogleAdsPanel getApi={getApi} /> */}
      {/* <MetaAdsPanel getApi={getApi} /> */}
      <SlackPanel getApi={getApi} />

      <McpPanel getApi={getApi} />

      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="w-full rounded-lg border-2 border-dashed border-gray-300 py-4 text-sm font-medium text-gray-500 hover:border-blue-400 hover:text-blue-600"
        >
          + Add another site
        </button>
      ) : (
        <div className="rounded-lg border border-gray-200 p-4 space-y-3">
          <input
            type="text"
            placeholder="Site name (e.g. Chowan University)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Domain (e.g. start.chowan.edu)"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              disabled={adding || !domain || !name}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {adding ? "Adding..." : "Add Site"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Usage Panel ──

function UsagePanel({
  userInfo,
  onUpgrade,
  onManageBilling,
}: {
  userInfo: UserInfo | null;
  onUpgrade: () => void;
  onManageBilling: () => void;
}) {
  if (!userInfo) return null;

  const pct = Math.min(100, Math.round((userInfo.usage_count / userInfo.usage_limit) * 100));
  const isPaid = userInfo.plan === "paid";

  return (
    <div className="space-y-6 p-4">
      <div className="rounded-lg border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900">Plan</h3>
        <p className="mt-1 text-2xl font-bold capitalize text-gray-900">
          {userInfo.plan === "past_due" ? "Past Due" : userInfo.plan}
        </p>
        <p className="mt-1 text-sm text-gray-500">{userInfo.email}</p>
      </div>

      <div className="rounded-lg border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900">Leads Scored</h3>
        <p className="mt-1 text-2xl font-bold text-gray-900">
          {userInfo.usage_count}
          {!isPaid && <span className="text-base font-normal text-gray-400"> / {userInfo.usage_limit}</span>}
        </p>
        {!isPaid && (
          <div className="mt-3">
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className={`h-2 rounded-full transition-all ${
                  pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-yellow-500" : "bg-blue-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {!isPaid ? (
        <button
          onClick={onUpgrade}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700"
        >
          Upgrade to Pro
        </button>
      ) : (
        <button
          onClick={onManageBilling}
          className="w-full rounded-lg bg-gray-100 px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-200"
        >
          Manage Billing
        </button>
      )}
    </div>
  );
}

// ── Google Ads Tab ──

function GoogleAdsTab({
  getApi,
  sites,
}: {
  getApi: () => Promise<ReturnType<typeof import("@/lib/api").createApi>>;
  sites: Site[];
}) {
  const [data, setData] = useState<CampaignPerformance | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [pulling, setPulling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasSiteWithGoogle = sites.some((s) => s.google_ads_customer_id);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const api = await getApi();
      const result = await api.getCampaignPerformance({ days });
      setData(result);
    } catch {
      setError("Failed to load campaign data.");
    } finally {
      setLoading(false);
    }
  }, [getApi, days]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const [pullMessage, setPullMessage] = useState<string | null>(null);

  const handlePullNow = async () => {
    setPulling(true);
    setPullMessage(null);
    try {
      const api = await getApi();
      await api.triggerJob("pull_google_ads");
      setPullMessage("Pull triggered — data will update within a few minutes.");
    } catch {
      setPullMessage("Failed to trigger pull. Please try again.");
    } finally {
      setPulling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!hasSiteWithGoogle && (!data || data.campaigns.length === 0)) {
    return (
      <div className="py-12 text-center px-4">
        <p className="text-sm text-gray-500">No Google Ads account connected.</p>
        <p className="text-xs text-gray-400 mt-1">Go to Setup to connect your Google Ads account.</p>
      </div>
    );
  }

  if (data && data.campaigns.length === 0) {
    return (
      <div className="py-12 text-center px-4">
        <p className="text-sm text-gray-500">No campaign data yet.</p>
        <p className="text-xs text-gray-400 mt-1">Data appears within 6 hours of connecting your Google Ads account.</p>
        {pullMessage ? (
          <p className="mt-3 text-sm text-blue-600">{pullMessage}</p>
        ) : (
          <button
            onClick={handlePullNow}
            disabled={pulling}
            className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {pulling ? "Pulling..." : "Pull Now"}
          </button>
        )}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="py-12 text-center text-sm text-red-500">{error || "Failed to load data."}</div>
    );
  }

  const fmt = (n: number) => `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div className="p-4 space-y-4">
      {/* Date range selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Google Ads Performance</h3>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-400">Total Spend</p>
          <p className="text-lg font-bold text-gray-900">{fmt(data.total_spend)}</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-400">Google Reported</p>
          <p className="text-lg font-bold text-gray-900">{data.total_google_reported}</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-400">EPI Verified</p>
          <p className="text-lg font-bold text-green-600">{data.total_epi_verified}</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3">
          <p className="text-xs text-gray-400">Junk Filtered</p>
          <p className="text-lg font-bold text-red-600">{data.total_junk}</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-3 col-span-2 sm:col-span-1">
          <p className="text-xs text-gray-400">Discrepancy</p>
          <p className="text-lg font-bold text-orange-600">
            {data.discrepancy_pct != null ? `${data.discrepancy_pct}%` : "N/A"}
          </p>
          {data.discrepancy_pct != null && data.discrepancy_pct > 0 && (
            <p className="text-xs text-orange-500">Google overcounted</p>
          )}
          {data.discrepancy_pct != null && data.discrepancy_pct < 0 && (
            <p className="text-xs text-blue-500">EPI found more leads</p>
          )}
        </div>
      </div>

      {/* Campaign table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs text-gray-500">
              <th className="px-3 py-2 font-medium">Campaign</th>
              <th className="px-3 py-2 font-medium">Ad Group</th>
              <th className="px-3 py-2 font-medium text-right">Spend</th>
              <th className="px-3 py-2 font-medium text-right">Clicks</th>
              <th className="px-3 py-2 font-medium text-right">Google</th>
              <th className="px-3 py-2 font-medium text-right">EPI Verified</th>
              <th className="px-3 py-2 font-medium text-right">Junk</th>
              <th className="px-3 py-2 font-medium text-right">Real CPL</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.campaigns.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-3 py-2 text-gray-900 font-medium">{row.campaign_name || "—"}</td>
                <td className="px-3 py-2 text-gray-600">{row.ad_group_name || "—"}</td>
                <td className="px-3 py-2 text-right text-gray-900">{fmt(row.spend)}</td>
                <td className="px-3 py-2 text-right text-gray-600">{row.clicks}</td>
                <td className="px-3 py-2 text-right text-gray-600">{row.google_reported}</td>
                <td className="px-3 py-2 text-right text-green-600 font-medium">{row.epi_verified}</td>
                <td className="px-3 py-2 text-right text-red-600">{row.junk}</td>
                <td className="px-3 py-2 text-right text-gray-900 font-medium">{row.real_cpl != null ? fmt(row.real_cpl) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Note about pixel if no EPI data */}
      {data.total_epi_verified === 0 && data.total_junk === 0 && data.campaigns.length > 0 && (
        <p className="text-xs text-gray-400 text-center">
          Install the EPI pixel on your landing pages to verify lead quality and see EPI-verified numbers.
        </p>
      )}
    </div>
  );
}

// ── Main Dashboard ──

export default function DashboardPage() {
  const { getApi } = useApi();
  const [tab, setTab] = useState<Tab>("leads");
  const [sites, setSites] = useState<Site[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [totalLeads, setTotalLeads] = useState(0);
  const [leadPage, setLeadPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);
  const [leadStats, setLeadStats] = useState<LeadStats | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [pixelStatuses, setPixelStatuses] = useState<Record<string, PixelStatus>>({});
  const [loading, setLoading] = useState(true);

  const fetchAllPixelStatuses = useCallback(async (siteList: Site[]) => {
    try {
      const api = await getApi();
      const results = await Promise.all(
        siteList.map(async (site) => {
          try {
            const status = await api.getPixelStatus(site.id);
            return [site.id, status] as const;
          } catch {
            return null;
          }
        })
      );
      const map: Record<string, PixelStatus> = {};
      for (const r of results) {
        if (r) map[r[0]] = r[1];
      }
      setPixelStatuses(map);
    } catch {}
  }, [getApi]);

  const fetchData = useCallback(async () => {
    try {
      const api = await getApi();
      const [sitesData, leadsData, me, stats] = await Promise.all([
        api.getSites(),
        api.getLeads({ page: 1, per_page: 25 }),
        api.getMe(),
        api.getLeadStats(),
      ]);
      setSites(sitesData);
      setLeads(leadsData.leads);
      setTotalLeads(leadsData.total);
      setLeadPage(1);
      setUserInfo(me);
      setLeadStats(stats);
      if (sitesData.length === 0) setTab("setup");
      if (sitesData.length > 0) {
        fetchAllPixelStatuses(sitesData);
      }
    } catch {
      // Will redirect to sign-in via middleware
    } finally {
      setLoading(false);
    }
  }, [getApi, fetchAllPixelStatuses]);

  const handleLoadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const api = await getApi();
      const nextPage = leadPage + 1;
      const result = await api.getLeads({ page: nextPage, per_page: 25 });
      setLeads((prev) => [...prev, ...result.leads]);
    } catch {
      // surface error so users know the load failed
      console.error("Failed to load more leads");
    } finally {
    }
  }, [getApi, leadPage]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Poll pixel statuses every 30 seconds
  useEffect(() => {
    if (sites.length === 0) return;
    const interval = setInterval(() => fetchAllPixelStatuses(sites), 30000);
    return () => clearInterval(interval);
  }, [sites, fetchAllPixelStatuses]);

  // Poll for pixel verification if any site is pending
  useEffect(() => {
    const hasPending = sites.some((s) => !s.pixel_verified);
    if (!hasPending) return;
    const interval = setInterval(async () => {
      try {
        const api = await getApi();
        const updated = await api.getSites();
        setSites(updated);
      } catch {}
    }, 5000);
    return () => clearInterval(interval);
  }, [sites, getApi]);

  const handleAddSite = async (domain: string, name: string) => {
    const api = await getApi();
    await api.createSite(domain, name);
    const updated = await api.getSites();
    setSites(updated);
  };

  const handleUpgrade = async () => {
    const api = await getApi();
    const { checkout_url } = await api.createCheckout();
    window.location.href = checkout_url;
  };

  const handleManageBilling = async () => {
    const api = await getApi();
    const { portal_url } = await api.getBillingPortal();
    window.location.href = portal_url;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "leads", label: "Leads" },
    { id: "google_ads", label: "Google Ads" },
    { id: "setup", label: "Setup" },
    { id: "usage", label: "Usage" },
  ];

  const showWarning =
    userInfo &&
    userInfo.plan === "free" &&
    userInfo.usage_count >= userInfo.usage_limit * 0.9;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <h1 className="text-lg font-bold text-gray-900">EPI</h1>
          <UserButton />
        </div>
      </header>

      {showWarning && (
        <div className="bg-amber-50 border-b border-amber-200">
          <div className="mx-auto max-w-3xl px-4 py-2 text-sm text-amber-800">
            {userInfo!.usage_count >= userInfo!.usage_limit
              ? "You've hit your free limit. Leads are being logged but not scored. "
              : `You've used ${userInfo!.usage_count} of ${userInfo!.usage_limit} free lead scores. `}
            <button onClick={handleUpgrade} className="font-semibold underline">
              Upgrade now
            </button>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-3xl px-4 py-6">
        {/* Tabs */}
        <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition ${
                tab === t.id
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="rounded-xl bg-white shadow-sm overflow-hidden">
          {tab === "leads" && (
            <>
              <PixelStatusBar sites={sites} statuses={pixelStatuses} />
              <LeadFeed
                leads={leads}
                userInfo={userInfo}
                sites={sites}
                totalLeads={totalLeads}
                onLoadMore={handleLoadMore}
                loadingMore={loadingMore}
                stats={leadStats}
              />
            </>
          )}
          {tab === "google_ads" && <GoogleAdsTab getApi={getApi} sites={sites} />}
          {tab === "setup" && <SetupPanel sites={sites} onAddSite={handleAddSite} pixelStatuses={pixelStatuses} getApi={getApi} />}
          {tab === "usage" && (
            <UsagePanel
              userInfo={userInfo}
              onUpgrade={handleUpgrade}
              onManageBilling={handleManageBilling}
            />
          )}
        </div>
      </div>
    </div>
  );
}
