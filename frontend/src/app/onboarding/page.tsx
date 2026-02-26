"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OnboardingIndex() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/onboarding/add-site");
  }, [router]);

  return (
    <div className="flex items-center justify-center py-12">
      <p className="text-gray-500">Loading setup wizard...</p>
    </div>
  );
}
