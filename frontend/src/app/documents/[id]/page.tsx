"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Download, FileText } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import ChunkViewer from "@/components/ChunkViewer";
import EntityList from "@/components/EntityList";
import EmptyState from "@/components/EmptyState";
import ErrorMessage from "@/components/ErrorMessage";
import { ChunkSkeleton, CardSkeleton } from "@/components/LoadingSkeleton";
import { FormatBadge } from "@/components/StatusBadge";
import { apiClient } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/format";
import type { Chunk, DocumentDetail } from "@/types";

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, docChunks] = await Promise.all([
        apiClient.getDocument(id),
        apiClient.getChunks(id),
      ]);
      setDoc(detail);
      setChunks(docChunks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <div className="space-y-6">
      <Link
        href="/documents"
        className="inline-flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to documents
      </Link>

      {error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : loading ? (
        <div className="space-y-4">
          <CardSkeleton />
          <ChunkSkeleton />
          <ChunkSkeleton />
        </div>
      ) : doc ? (
        <>
          <header className="card">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="truncate text-xl font-bold tracking-tight text-gray-900">
                    {doc.title || doc.filename}
                  </h1>
                  <FormatBadge format={doc.format} />
                </div>
                <p className="mt-1 font-mono text-sm text-gray-500">
                  {doc.filename}
                </p>
              </div>
              <a
                href={apiClient.exportUrl(doc.id)}
                target="_blank"
                rel="noreferrer"
                className="btn-secondary flex-shrink-0"
              >
                <Download className="h-4 w-4" />
                Export JSONL
              </a>
            </div>

            <dl className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Meta label="Chunks" value={String(doc.total_chunks)} />
              <Meta label="Words" value={doc.word_count.toLocaleString()} />
              <Meta label="Size" value={formatBytes(doc.file_size_bytes)} />
              <Meta label="Author" value={doc.author || "—"} />
            </dl>
            <p className="mt-3 text-xs text-gray-400">
              Ingested {formatDate(doc.created_at)} · hash{" "}
              <span className="font-mono">{doc.content_hash.slice(0, 12)}…</span>
            </p>
          </header>

          <div className="grid gap-6 lg:grid-cols-3">
            <section className="lg:col-span-2">
              <h2 className="mb-3 text-sm font-semibold text-gray-900">
                Chunks ({chunks.length})
              </h2>
              {chunks.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No chunks"
                  description="This document produced no chunks."
                />
              ) : (
                <ChunkViewer chunks={chunks} />
              )}
            </section>

            <aside className="space-y-4">
              <div className="card">
                <h2 className="mb-3 text-sm font-semibold text-gray-900">
                  Entities
                </h2>
                <EntityList entities={doc.entities} />
              </div>
              {doc.metadata?.dates && doc.metadata.dates.length > 0 && (
                <div className="card">
                  <h2 className="mb-3 text-sm font-semibold text-gray-900">
                    Dates found
                  </h2>
                  <div className="flex flex-wrap gap-1.5">
                    {doc.metadata.dates.map((d) => (
                      <span
                        key={d}
                        className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </aside>
          </div>
        </>
      ) : (
        <EmptyState title="Document not found" />
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-gray-400">{label}</dt>
      <dd className="mt-0.5 truncate text-sm font-semibold text-gray-900">
        {value}
      </dd>
    </div>
  );
}
