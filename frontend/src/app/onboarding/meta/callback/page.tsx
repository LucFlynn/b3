"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function MetaCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error) {
      setStatus("error");
      setErrorMsg(error);
      return;
    }

    if (code) {
      localStorage.setItem("epi_meta_token", code);
      setStatus("success");
      setTimeout(() => {
        router.push("/onboarding/slack");
      }, 1500);
    } else {
      setStatus("error");
      setErrorMsg("No authorization code received");
    }
  }, [searchParams, router]);

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-4 text-xl font-bold text-gray-900">
        Meta Ads Connection
      </h2>

      {status === "loading" && (
        <div className="flex items-center gap-3 py-8">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          <p className="text-sm text-gray-500">
            Processing authorization...
          </p>
        </div>
      )}

      {status === "success" && (
        <div className="py-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <svg
              className="h-6 w-6 text-green-600"
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
            Meta Ads connected successfully!
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Redirecting to next step...
          </p>
        </div>
      )}

      {status === "error" && (
        <div className="py-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <p className="text-sm font-medium text-red-700">
            Connection failed: {errorMsg}
          </p>
          <button
            onClick={() => router.push("/onboarding/meta")}
            className="mt-4 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
