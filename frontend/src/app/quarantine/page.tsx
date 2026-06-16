"use client";

import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import QuarantineList from "@/components/QuarantineList";
import EmptyState from "@/components/EmptyState";
import ErrorMessage from "@/components/ErrorMessage";
import { ListSkeleton } from "@/components/LoadingSkeleton";
import { apiClient } from "@/lib/api";
import type { QuarantineEntry } from "@/types";

export default function QuarantinePage() {
  const [entries, setEntries] = useState<QuarantineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reprocessing, setReprocessing] = useState<Record<string, boolean>>({});
  const [notice, setNotice] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setEntries(await apiClient.listQuarantine());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load quarantine");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleReprocess = async (id: string) => {
    setReprocessing((prev) => ({ ...prev, [id]: true }));
    setNotice(null);
    try {
      const result = await apiClient.reprocessQuarantine(id);
      if (result.status === "quarantined") {
        setNotice(`Reprocessing failed again: ${result.error ?? "unknown error"}`);
      } else {
        setNotice(`Reprocessed “${result.filename}” — status: ${result.status}.`);
        setEntries((prev) => prev.filter((e) => e.id !== id));
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Reprocess failed");
    } finally {
      setReprocessing((prev) => ({ ...prev, [id]: false }));
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Quarantine
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Files that failed parsing or processing. Reprocess them after fixing
          the source.
        </p>
      </header>

      {notice && (
        <div className="rounded-xl border border-brand-100 bg-brand-50 p-3 text-sm text-brand-700">
          {notice}
        </div>
      )}

      {error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : loading ? (
        <ListSkeleton rows={3} />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={ShieldCheck}
          title="Quarantine is empty"
          description="No files have failed processing. Failed ingestions will appear here for review."
        />
      ) : (
        <QuarantineList
          entries={entries}
          onReprocess={handleReprocess}
          reprocessing={reprocessing}
        />
      )}
    </div>
  );
}
