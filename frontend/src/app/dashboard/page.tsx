"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, Site } from "@/lib/api";
import { RequireAuth } from "@/lib/require-auth";

function StatusBadge({
  connected,
  label,
}: {
  connected: boolean;
  label: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
        connected
          ? "bg-green-100 text-green-700"
          : "bg-gray-100 text-gray-500"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${
          connected ? "bg-green-500" : "bg-gray-300"
        }`}
      />
      {label}
    </span>
  );
}

function DashboardContent() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [sites, setSites] = useState<Site[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    api
      .getSites()
      .then((data) => setSites(data))
      .catch(() => {})
      .finally(() => setFetching(false));
  }, []);

  if (fetching) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-lg font-bold text-gray-900">EPI Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={() => {
                logout();
                router.push("/auth/login");
              }}
              className="rounded-md bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-600 transition hover:bg-gray-200"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {/* Summary cards */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm font-medium text-gray-500">Total Sites</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">
              {sites.length}
            </p>
          </div>
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm font-medium text-gray-500">
              Verified Pixels
            </p>
            <p className="mt-1 text-3xl font-bold text-green-600">
              {sites.filter((s) => s.pixel_verified).length}
            </p>
          </div>
          <div className="rounded-xl bg-white p-6 shadow-sm">
            <p className="text-sm font-medium text-gray-500">
              Total Leads
            </p>
            <p className="mt-1 text-3xl font-bold text-blue-600">
              {sites.reduce((sum, s) => sum + (s.leads_count || 0), 0)}
            </p>
          </div>
        </div>

        {/* Sites list */}
        <div className="rounded-xl bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
            <h2 className="text-base font-semibold text-gray-900">Sites</h2>
            <button
              onClick={() => router.push("/onboarding/add-site")}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
            >
              Add Site
            </button>
          </div>

          {sites.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-sm text-gray-500">
                No sites yet. Add your first site to get started.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {sites.map((site) => (
                <div
                  key={site.id}
                  className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900">
                      {site.name}
                    </h3>
                    <p className="text-xs text-gray-400">{site.domain}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge
                      connected={site.pixel_verified}
                      label="Pixel"
                    />
                    <span className="ml-2 text-xs text-gray-400">
                      {site.leads_count ?? 0} leads
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
