const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("epi_token");
}

function setToken(token: string): void {
  localStorage.setItem("epi_token", token);
}

function clearToken(): void {
  localStorage.removeItem("epi_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

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

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  agency_id: string;
  role: string;
}

export interface Site {
  id: string;
  domain: string;
  name: string;
  pixel_id: string;
  pixel_verified: boolean;
  pixel_snippet?: string;
  leads_count?: number;
}

export const api = {
  register: async (
    email: string,
    password: string,
    agencyName: string,
    inviteCode: string
  ): Promise<AuthResponse> => {
    const data = await request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        agency_name: agencyName,
        invite_code: inviteCode,
      }),
    });
    setToken(data.access_token);
    return data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const data = await request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    return data;
  },

  getMe: async (): Promise<User> => {
    return request<User>("/api/auth/me");
  },

  createSite: async (domain: string, name: string): Promise<Site> => {
    return request<Site>("/api/sites", {
      method: "POST",
      body: JSON.stringify({ domain, name }),
    });
  },

  getSites: async (): Promise<Site[]> => {
    return request<Site[]>("/api/sites");
  },

  getToken,
  setToken,
  clearToken,
};
