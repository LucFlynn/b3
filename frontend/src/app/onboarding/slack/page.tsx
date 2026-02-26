"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const SLACK_INSTALL_URL =
  process.env.NEXT_PUBLIC_SLACK_INSTALL_URL ||
  "http://localhost:8000/oauth/slack/authorize";

export default function SlackPage() {
  const router = useRouter();
  const [installed, setInstalled] = useState(false);

  const handleInstall = () => {
    // Open Slack install in a popup/new tab
    const popup = window.open(SLACK_INSTALL_URL, "slack_install", "width=600,height=700");

    // Poll for popup close
    const interval = setInterval(() => {
      if (popup && popup.closed) {
        clearInterval(interval);
        setInstalled(true);
        localStorage.setItem("epi_slack_connected", "true");
      }
    }, 500);
  };

  const handleContinue = () => {
    router.push("/onboarding/verify");
  };

  const handleSkip = () => {
    router.push("/onboarding/verify");
  };

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Step 4: Install Slack Bot
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Get real-time lead notifications delivered straight to your Slack
        channel.
      </p>

      <div className="flex flex-col items-center gap-4 py-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-purple-50">
          <svg
            className="h-8 w-8 text-purple-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
            />
          </svg>
        </div>

        {!installed ? (
          <button
            onClick={handleInstall}
            className="rounded-lg bg-purple-600 px-8 py-3 text-sm font-semibold text-white transition hover:bg-purple-700"
          >
            Install Slack Bot
          </button>
        ) : (
          <div className="text-center">
            <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-5 w-5 text-green-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p className="text-sm font-medium text-green-700">
              Slack bot installed!
            </p>
            <button
              onClick={handleContinue}
              className="mt-4 rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
            >
              Continue
            </button>
          </div>
        )}
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
