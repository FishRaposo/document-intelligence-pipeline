import Link from "next/link";
import { ArrowRight, CheckCircle2, Copy, ShieldAlert } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { IngestResult } from "@/types";

export default function IngestResultCard({ result }: { result: IngestResult }) {
  const isQuarantined = result.status === "quarantined";

  return (
    <div
      data-testid="ingest-result"
      className="card space-y-4 border-l-4"
      style={{
        borderLeftColor: isQuarantined ? "#ef4444" : "#10b981",
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isQuarantined ? (
            <ShieldAlert className="h-5 w-5 text-red-500" />
          ) : result.status === "duplicate" ? (
            <Copy className="h-5 w-5 text-amber-500" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          )}
          <span className="font-mono text-sm text-gray-900">
            {result.filename}
          </span>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {isQuarantined ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {result.error || "The document failed processing and was quarantined."}
        </p>
      ) : (
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <Field label="Title" value={result.title || "—"} />
          <Field label="Chunks" value={String(result.total_chunks)} />
          <Field
            label="Words"
            value={String(result.metadata?.word_count ?? "—")}
          />
        </dl>
      )}

      {result.document_id && (
        <Link
          href={`/documents/${result.document_id}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          View document
          <ArrowRight className="h-4 w-4" />
        </Link>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-gray-400">{label}</dt>
      <dd className="mt-0.5 truncate font-medium text-gray-900">{value}</dd>
    </div>
  );
}
