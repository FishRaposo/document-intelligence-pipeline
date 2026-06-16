"use client";

import { useEffect, useState } from "react";
import { FlaskConical } from "lucide-react";
import { demoState } from "@/lib/api";

/**
 * Visible "Demo mode" indicator. Subscribes to the API client's demo state,
 * which flips to true whenever a live request fails and a mock fallback is used.
 */
export default function DemoModeBadge() {
  const [demo, setDemo] = useState(false);

  useEffect(() => {
    const unsubscribe = demoState.subscribe(setDemo);
    return () => {
      unsubscribe();
    };
  }, []);

  if (!demo) return null;

  return (
    <span
      data-testid="demo-mode-badge"
      title="No backend reachable — showing bundled sample data."
      className="inline-flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700"
    >
      <FlaskConical className="h-3.5 w-3.5" />
      Demo mode
    </span>
  );
}
