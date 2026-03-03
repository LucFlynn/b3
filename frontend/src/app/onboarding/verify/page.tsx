"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function VerifyPixelPage() {
  const router = useRouter();
  const [verified, setVerified] = useState(false);
  const [checking, setChecking] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkVerification = useCallback(async () => {
    setChecking(true);
    try {
      const sites = await api.getSites();
      if (sites.length > 0 && sites[0].pixel_verified) {
        setVerified(true);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch {
      // Silently fail
    } finally {
      setChecking(false);
    }
  }, []);

  // Poll every 5 seconds
  useEffect(() => {
    checkVerification();
    intervalRef.current = setInterval(checkVerification, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [checkVerification]);

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Verify Pixel Installation
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Visit your site in a browser to trigger the pixel. We&apos;ll detect it
        automatically.
      </p>

      {/* Verification status */}
      <div className="mb-6 rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`h-3 w-3 rounded-full ${
                verified ? "bg-green-500" : "bg-yellow-400 animate-pulse"
              }`}
            />
            <span className="text-sm font-medium text-gray-700">
              {verified
                ? "Pixel verified! We are receiving data."
                : "Waiting for pixel verification..."}
            </span>
          </div>
          {!verified && (
            <button
              onClick={checkVerification}
              disabled={checking}
              className="rounded-md bg-gray-100 px-4 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-200 disabled:opacity-50"
            >
              {checking ? "Checking..." : "Check Now"}
            </button>
          )}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-end">
        <button
          onClick={() => router.push("/dashboard")}
          className={`rounded-lg px-6 py-2.5 text-sm font-semibold text-white transition ${
            verified
              ? "bg-green-600 hover:bg-green-700"
              : "bg-gray-400 hover:bg-gray-500"
          }`}
        >
          {verified ? "Go to Dashboard" : "Skip for now"}
        </button>
      </div>
    </div>
  );
}
