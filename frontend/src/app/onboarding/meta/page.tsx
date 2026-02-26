"use client";

import { useRouter } from "next/navigation";

const META_OAUTH_URL =
  process.env.NEXT_PUBLIC_META_OAUTH_URL ||
  "http://localhost:8000/oauth/meta/authorize";

export default function MetaAdsPage() {
  const router = useRouter();

  const handleConnect = () => {
    const redirectUri = `${window.location.origin}/onboarding/meta/callback`;
    const url = `${META_OAUTH_URL}?redirect_uri=${encodeURIComponent(redirectUri)}`;
    window.location.href = url;
  };

  const handleSkip = () => {
    router.push("/onboarding/slack");
  };

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Step 3: Connect Meta Ads
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Link your Meta (Facebook/Instagram) Ads account to track social ad
        performance.
      </p>

      <div className="flex flex-col items-center gap-4 py-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-indigo-50">
          <svg
            className="h-8 w-8 text-indigo-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.5 7.5h-.75A2.25 2.25 0 004.5 9.75v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75m-6 3.75l3 3m0 0l3-3m-3 3V1.5"
            />
          </svg>
        </div>

        <button
          onClick={handleConnect}
          className="rounded-lg bg-indigo-600 px-8 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
        >
          Connect Meta Ads
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
