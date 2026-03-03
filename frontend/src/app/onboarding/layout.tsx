"use client";

import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { RequireAuth } from "@/lib/require-auth";

const STEPS = [
  { path: "/onboarding/add-site", label: "Add Site", number: 1 },
  { path: "/onboarding/install-pixel", label: "Install Pixel", number: 2 },
  { path: "/onboarding/verify", label: "Verify", number: 3 },
];

function getCurrentStep(pathname: string): number {
  for (const step of STEPS) {
    if (pathname.startsWith(step.path)) return step.number;
  }
  return 1;
}

export default function OnboardingLayout({
  children,
}: {
  children: ReactNode;
}) {
  const pathname = usePathname();
  const currentStep = getCurrentStep(pathname);

  return (
    <RequireAuth>
      <div className="min-h-screen bg-gray-50">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto max-w-3xl px-4 py-4">
            <h1 className="text-lg font-bold text-gray-900">EPI Setup</h1>
          </div>
        </header>

        {/* Step indicator */}
        <div className="mx-auto max-w-3xl px-4 pt-8 pb-4">
          <nav aria-label="Onboarding progress">
            <ol className="flex items-center gap-2">
              {STEPS.map((step) => {
                const isActive = step.number === currentStep;
                const isComplete = step.number < currentStep;
                return (
                  <li key={step.number} className="flex flex-1 items-center">
                    <div className="flex w-full flex-col items-center gap-1">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold transition ${
                          isActive
                            ? "bg-blue-600 text-white"
                            : isComplete
                            ? "bg-green-500 text-white"
                            : "bg-gray-200 text-gray-500"
                        }`}
                      >
                        {isComplete ? (
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={3}
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        ) : (
                          step.number
                        )}
                      </div>
                      <span
                        className={`text-xs font-medium ${
                          isActive
                            ? "text-blue-600"
                            : isComplete
                            ? "text-green-600"
                            : "text-gray-400"
                        }`}
                      >
                        {step.label}
                      </span>
                    </div>
                    {step.number < STEPS.length && (
                      <div
                        className={`mx-1 h-0.5 flex-1 ${
                          step.number < currentStep
                            ? "bg-green-400"
                            : "bg-gray-200"
                        }`}
                      />
                    )}
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>

        {/* Step content */}
        <main className="mx-auto max-w-3xl px-4 py-6">{children}</main>
      </div>
    </RequireAuth>
  );
}
