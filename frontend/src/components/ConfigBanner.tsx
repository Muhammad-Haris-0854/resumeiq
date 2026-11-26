import { AlertTriangle } from "lucide-react";

import { apiConfigured, missingConfig } from "@/lib/env";

/**
 * Shown when a build is missing configuration, e.g. the static GitHub Pages preview which ships
 * the UI and Supabase auth but has no FastAPI service behind it.
 */
export function ConfigBanner() {
  if (missingConfig.length === 0 && apiConfigured) return null;

  const reasons = [
    ...(missingConfig.length > 0 ? [`missing ${missingConfig.join(", ")}`] : []),
    ...(apiConfigured ? [] : ["no API endpoint in this build"]),
  ];

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex justify-center px-4">
      <div className="pointer-events-auto flex max-w-xl items-start gap-3 rounded-xl border border-amber-300/70 bg-amber-50 px-4 py-3 text-sm text-amber-900 shadow-lg">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          <span className="font-semibold">Preview build:</span> {reasons.join(", ")}. Sign-in works;
          resume analysis needs the FastAPI service (see the README).
        </p>
      </div>
    </div>
  );
}
