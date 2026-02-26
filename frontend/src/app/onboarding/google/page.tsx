"use client";

import { useRouter } from "next/navigation";

const GOOGLE_OAUTH_URL =
  process.env.NEXT_PUBLIC_GOOGLE_OAUTH_URL ||
  "http://localhost:8000/oauth/google/authorize";

export default function GoogleAdsPage() {
  const router = useRouter();

  const handleConnect = () => {
    const redirectUri = `${window.location.origin}/onboarding/google/callback`;
    const url = `${GOOGLE_OAUTH_URL}?redirect_uri=${encodeURIComponent(redirectUri)}`;
    window.location.href = url;
  };

  const handleSkip = () => {
    router.push("/onboarding/meta");
  };

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Step 2: Connect Google Ads
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Link your Google Ads account to automatically import campaign data and
        track ad spend.
      </p>

      <div className="flex flex-col items-center gap-4 py-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
          <svg
            className="h-8 w-8 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.86-2.54a4.5 4.5 0 00-6.364-6.364L4.5 8.06"
            />
          </svg>
        </div>

        <button
          onClick={handleConnect}
          className="rounded-lg bg-blue-600 px-8 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          Connect Google Ads
        </button>
      </div>

      <div className="flex justify-between border-t border-gray-100 pt-4">
        <button
          onClick={handleSkip}
          className="text-sm font-medium text-gray-400 transition hover:text-gray-600"
        >
          Skip for now
        </button>
      </div>
    </div>
  );
}
