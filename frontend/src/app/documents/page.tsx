"use client";

import { useEffect, useState } from "react";
import { FileText, Upload } from "lucide-react";
import Link from "next/link";
import DocumentList from "@/components/DocumentList";
import EmptyState from "@/components/EmptyState";
import ErrorMessage from "@/components/ErrorMessage";
import { ListSkeleton } from "@/components/LoadingSkeleton";
import { apiClient } from "@/lib/api";
import type { DocumentSummary } from "@/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setDocuments(await apiClient.listDocuments());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Documents
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {documents.length} ingested {documents.length === 1 ? "document" : "documents"}
          </p>
        </div>
        <Link href="/ingest" className="btn-primary">
          <Upload className="h-4 w-4" />
          Ingest
        </Link>
      </header>

      {error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : loading ? (
        <ListSkeleton rows={4} />
      ) : documents.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No documents yet"
          description="Ingest your first document to see parsed metadata, entities, and chunks here."
        >
          <Link href="/ingest" className="btn-primary">
            <Upload className="h-4 w-4" />
            Ingest a document
          </Link>
        </EmptyState>
      ) : (
        <DocumentList documents={documents} />
      )}
    </div>
  );
}
