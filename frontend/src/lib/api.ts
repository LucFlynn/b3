const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Site {
  id: string;
  domain: string;
  name: string;
  pixel_id: string;
  pixel_verified: boolean;
  pixel_snippet?: string;
  leads_count?: number;
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
      return request<Lead[]>(`/api/leads/recent${qs ? `?${qs}` : ""}`, token);
    },

    getLeadStats: () => request<Record<string, unknown>>("/api/leads/stats", token),

    createCheckout: () =>
      request<{ checkout_url: string }>("/api/billing/create-checkout", token, {
        method: "POST",
      }),

    getBillingPortal: () =>
      request<{ portal_url: string }>("/api/billing/portal", token),

    getPixelStatus: (siteId: string) =>
      request<PixelStatus>(`/api/sites/${siteId}/pixel-status`, token),
  };
}
