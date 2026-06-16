"use client";

import { useEffect, useState } from "react";
import {
  ArrowRight,
  FileText,
  Search,
  ShieldAlert,
  Upload,
} from "lucide-react";
import Link from "next/link";
import ProcessingStats from "@/components/ProcessingStats";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import ErrorMessage from "@/components/ErrorMessage";
import { apiClient } from "@/lib/api";
import type { DocumentSummary, QuarantineEntry } from "@/types";

const QUICK_LINKS = [
  {
    href: "/ingest",
    title: "Ingest a document",
    description: "Upload a file or paste text to run the pipeline.",
    icon: Upload,
  },
  {
    href: "/documents",
    title: "Browse documents",
    description: "Inspect parsed metadata, entities, and chunks.",
    icon: FileText,
  },
  {
    href: "/search",
    title: "Similarity search",
    description: "Query the vector index for ranked chunks.",
    icon: Search,
  },
  {
    href: "/quarantine",
    title: "Review quarantine",
    description: "Triage and reprocess failed files.",
    icon: ShieldAlert,
  },
];

export default function OverviewPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [quarantine, setQuarantine] = useState<QuarantineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [docs, quar] = await Promise.all([
        apiClient.listDocuments(),
        apiClient.listQuarantine(),
      ]);
      setDocuments(docs);
      setQuarantine(quar);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Overview
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Multi-stage ingestion: parse, clean, chunk, dedup, embed, and search —
          with an error quarantine for resilient batch processing.
        </p>
      </header>

      {error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : loading ? (
        <CardSkeleton />
      ) : (
        <ProcessingStats documents={documents} quarantine={quarantine} />
      )}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-900">Quick actions</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {QUICK_LINKS.map(({ href, title, description, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="group card flex items-start gap-4 transition-shadow hover:shadow-md"
            >
              <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Icon className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1 font-semibold text-gray-900">
                  {title}
                  <ArrowRight className="h-4 w-4 text-gray-300 transition group-hover:translate-x-0.5 group-hover:text-brand-500" />
                </span>
                <span className="mt-0.5 block text-sm text-gray-500">
                  {description}
                </span>
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
