const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Site {
  id: string;
  domain: string;
  name: string;
  pixel_id: string;
  pixel_verified: boolean;
  pixel_snippet?: string;
  leads_count?: number;
  google_ads_customer_id?: string;
  meta_ads_account_id?: string;
}

export interface ScoringSignal {
  signal: string;
  points: number;
  detail: string;
}

export interface Lead {
  id: string;
  site_id: string;
  visitor_id: string;
  name?: string;
  email?: string;
  phone?: string;
  email_valid?: string;
  phone_valid?: string;
  is_bot: boolean;
  honeypot_triggered?: boolean;
  form_fill_time_ms?: number;
  quality_score?: number;
  quality_label?: string;
  attribution_tier?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  gclid?: string;
  fbclid?: string;
  is_duplicate: boolean;
  page_url?: string;
  created_at: string;
  scoring_signals?: {
    signals_fired: ScoringSignal[];
    checks: {
      email: { status: string | null; provided: boolean };
      phone: { status: string | null; provided: boolean };
      bot: { is_bot: boolean; honeypot: boolean; form_fill_ms: number | null; user_agent_bot: boolean; reasons: string[] };
      ip: { vpn: boolean; proxy: boolean; tor: boolean; datacenter: boolean; country: string };
      attribution: { tier: string; gclid: string | null; fbclid: string | null; utm_source: string | null; utm_medium: string | null; utm_campaign: string | null; referrer: string | null };
    };
    dedup: { is_duplicate: boolean; reason?: string; first_seen?: string; count?: number };
  };
}

export interface PixelStatus {
  pixel_status: "active" | "idle" | "inactive" | "waiting";
  last_event_at: string | null;
  page_views_today: number;
}

export interface UserInfo {
  id: string;
  email: string;
  agency_id: string;
  role: string;
  plan: string;
  usage_count: number;
  usage_limit: number;
}

export interface GoogleAdsConnection {
  id: string;
  customer_id: string;
  account_name: string;
  connected_at: string | null;
  last_used_at: string | null;
  status: string;
}

export interface MetaAdsConnection {
  id: string;
  account_id: string;
  account_name: string;
  connected_at: string | null;
  last_used_at: string | null;
  status: string;
}

export interface SlackConnection {
  id: string;
  workspace_id: string;
  workspace_name: string;
  channel_name: string;
  connected_at: string | null;
  status: string;
}

export interface PaginatedLeads {
  leads: Lead[];
  total: number;
  page: number;
  per_page: number;
}

export interface LeadStats {
  total_leads: number;
  verified: number;
  likely_real: number;
  suspicious: number;
  junk: number;
  duplicates: number;
  attributed: number;
  unattributed: number;
  avg_quality_score: number | null;
}

export interface CampaignRow {
  campaign_name: string | null;
  ad_group_name: string | null;
  spend: number;
  clicks: number;
  google_reported: number;
  epi_verified: number;
  junk: number;
  real_cpl: number | null;
}

export interface CampaignPerformance {
  total_spend: number;
  total_google_reported: number;
  total_epi_verified: number;
  total_junk: number;
  discrepancy_pct: number | null;
  campaigns: CampaignRow[];
}

async function request<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `Request failed: ${res.status}`);
  }

  return res.json();
}

export function createApi(token: string) {
  return {
    getMe: () => request<UserInfo>("/api/auth/me", token),

    createSite: (domain: string, name: string) =>
      request<Site>("/api/sites", token, {
        method: "POST",
        body: JSON.stringify({ domain, name }),
      }),

    getSites: () => request<Site[]>("/api/sites", token),

    getLeads: (params?: { site_id?: string; page?: number; per_page?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.site_id) searchParams.set("site_id", params.site_id);
      if (params?.page) searchParams.set("page", String(params.page));
      if (params?.per_page) searchParams.set("per_page", String(params.per_page));
      const qs = searchParams.toString();
      return request<PaginatedLeads>(`/api/leads${qs ? `?${qs}` : ""}`, token);
    },

    getLeadStats: () => request<LeadStats>("/api/leads/stats", token),

    createCheckout: () =>
      request<{ checkout_url: string }>("/api/billing/create-checkout", token, {
        method: "POST",
      }),

    getBillingPortal: () =>
      request<{ portal_url: string }>("/api/billing/portal", token),

    getPixelStatus: (siteId: string) =>
      request<PixelStatus>(`/api/sites/${siteId}/pixel-status`, token),

    generateApiKey: () =>
      request<{ api_key: string }>("/api/auth/api-key", token, { method: "POST" }),

    getGoogleAdsAuthUrl: () =>
      request<{ auth_url: string }>("/api/google-ads/auth-url", token),

    getGoogleAdsConnections: () =>
      request<GoogleAdsConnection[]>("/api/google-ads/connections", token),

    disconnectGoogleAds: (connectionId: string) =>
      request<{ status: string }>(`/api/google-ads/disconnect/${connectionId}`, token, {
        method: "POST",
      }),

    selectGoogleAdsAccount: (connectionId: string, customerId: string, accountName: string) =>
      request<{ status: string }>(`/api/google-ads/select-account?connection_id=${connectionId}&customer_id=${customerId}&account_name=${encodeURIComponent(accountName)}`, token, {
        method: "POST",
      }),

    getGoogleAdsPendingAccounts: (connectionId: string) =>
      request<{ connection_id: string; accounts: { customer_id: string; descriptive_name: string }[] }>(`/api/google-ads/pending-accounts/${connectionId}`, token),

    // Meta Ads
    getMetaAdsAuthUrl: () =>
      request<{ auth_url: string }>("/api/meta-ads/auth-url", token),

    getMetaAdsConnections: () =>
      request<MetaAdsConnection[]>("/api/meta-ads/connections", token),

    disconnectMetaAds: (connectionId: string) =>
      request<{ status: string }>(`/api/meta-ads/disconnect/${connectionId}`, token, {
        method: "POST",
      }),

    getMetaAdsPendingAccounts: (connectionId: string) =>
      request<{ connection_id: string; accounts: { account_id: string; name: string }[] }>(`/api/meta-ads/pending-accounts/${connectionId}`, token),

    selectMetaAdsAccount: (connectionId: string, accountId: string, accountName: string) =>
      request<{ status: string }>(`/api/meta-ads/select-account?connection_id=${connectionId}&account_id=${accountId}&account_name=${encodeURIComponent(accountName)}`, token, {
        method: "POST",
      }),

    // Slack
    getSlackInstallUrl: () =>
      request<{ install_url: string }>("/api/slack/install-url", token),

    getSlackConnections: () =>
      request<SlackConnection[]>("/api/slack/connections", token),

    disconnectSlack: (connectionId: string) =>
      request<{ status: string }>(`/api/slack/disconnect/${connectionId}`, token, {
        method: "POST",
      }),

    getCampaignPerformance: (params?: { site_id?: string; days?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.site_id) searchParams.set("site_id", params.site_id);
      if (params?.days) searchParams.set("days", String(params.days));
      const qs = searchParams.toString();
      return request<CampaignPerformance>(`/api/campaigns/performance${qs ? `?${qs}` : ""}`, token);
    },

    triggerJob: (jobName: string) =>
      request<{ status: string }>(`/api/jobs/run/${jobName}`, token, { method: "POST" }),
  };
}
