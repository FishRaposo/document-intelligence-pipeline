"use client";

import { Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import { FormatBadge } from "@/components/StatusBadge";
import { formatBytes, formatDate } from "@/lib/format";
import type { QuarantineEntry } from "@/types";

interface QuarantineListProps {
  entries: QuarantineEntry[];
  onReprocess?: (id: string) => void;
  reprocessing?: Record<string, boolean>;
}

export default function QuarantineList({
  entries,
  onReprocess,
  reprocessing = {},
}: QuarantineListProps) {
  return (
    <ul className="space-y-3" data-testid="quarantine-list">
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="flex min-w-0 items-start gap-3">
            <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-500">
              <ShieldAlert className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="truncate font-mono text-sm font-semibold text-gray-900">
                  {entry.filename}
                </h3>
                <FormatBadge format={entry.format} />
              </div>
              <p className="mt-0.5 text-sm text-red-600">{entry.reason}</p>
              <p className="mt-0.5 text-xs text-gray-400">
                {formatBytes(entry.file_size_bytes)} · {formatDate(entry.created_at)}
              </p>
            </div>
          </div>
          {onReprocess && (
            <button
              onClick={() => onReprocess(entry.id)}
              disabled={reprocessing[entry.id]}
              className="btn-secondary flex-shrink-0"
            >
              {reprocessing[entry.id] ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Reprocess
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
