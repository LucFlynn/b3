"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, Site } from "@/lib/api";

export default function InstallPixelPage() {
  const router = useRouter();
  const [site, setSite] = useState<Site | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getSites().then((sites) => {
      if (sites.length > 0) {
        setSite(sites[0]);
      }
    });
  }, []);

  const snippet = site?.pixel_snippet || "";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(snippet);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = snippet;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl bg-white p-8 shadow-lg">
      <h2 className="mb-2 text-xl font-bold text-gray-900">
        Install Tracking Pixel
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
            {snippet || "Loading..."}
          </pre>
          <button
            onClick={handleCopy}
            disabled={!snippet}
            className="absolute top-2 right-2 rounded-md bg-gray-700 px-3 py-1.5 text-xs font-medium text-gray-200 transition hover:bg-gray-600"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => router.push("/onboarding/verify")}
          className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          I&apos;ve installed it &mdash; Verify
        </button>
      </div>
    </div>
  );
}
