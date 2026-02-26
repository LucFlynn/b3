"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function VerifyPixelPage() {
  const router = useRouter();
  const [pixelSnippet, setPixelSnippet] = useState("");
  const [copied, setCopied] = useState(false);
  const [verified, setVerified] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    // Generate pixel snippet based on first site
    api.getSites().then((sites) => {
      if (sites.length > 0) {
        const site = sites[0];
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        setPixelSnippet(
          `<script src="${apiUrl}/pixel/p.js" data-site-id="${site.id}"></script>`
        );
        setVerified(site.pixel_verified);
      }
    });
  }, []);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pixelSnippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback copy
      const textarea = document.createElement("textarea");
      textarea.value = pixelSnippet;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const checkVerification = useCallback(async () => {
    setChecking(true);
    try {
      const sites = await api.getSites();
      if (sites.length > 0 && sites[0].pixel_verified) {
        setVerified(true);
      }
    } catch {
      // Silently fail
    } finally {
      setChecking(false);
    }
  }, []);

  const handleFinish = () => {
    router.push("/dashboard");
  };

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Step 5: Install Tracking Pixel
      </h2>
      <p className="mb-6 text-sm text-gray-500">
        Add this snippet to your site&apos;s HTML, right before the closing{" "}
        <code className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono">
          &lt;/head&gt;
        </code>{" "}
        tag.
      </p>

      {/* Pixel snippet */}
      <div className="mb-6">
        <div className="relative">
          <pre className="overflow-x-auto rounded-lg bg-gray-900 p-4 text-sm text-green-400 font-mono">
            {pixelSnippet || "Loading..."}
          </pre>
          <button
            onClick={handleCopy}
            disabled={!pixelSnippet}
            className="absolute top-2 right-2 rounded-md bg-gray-700 px-3 py-1.5 text-xs font-medium text-gray-200 transition hover:bg-gray-600"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      {/* Verification status */}
      <div className="mb-6 rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`h-3 w-3 rounded-full ${
                verified ? "bg-green-500" : "bg-yellow-400"
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

      {/* Finish */}
      <div className="flex justify-end">
        <button
          onClick={handleFinish}
          className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          {verified ? "Go to Dashboard" : "Finish Setup"}
        </button>
      </div>
    </div>
  );
}
