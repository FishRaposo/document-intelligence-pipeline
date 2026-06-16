import Link from "next/link";
import { FileText } from "lucide-react";
import { formatScore } from "@/lib/format";
import type { SearchHit } from "@/types";

export default function SearchResults({ hits }: { hits: SearchHit[] }) {
  return (
    <ol className="space-y-3" data-testid="search-results">
      {hits.map((hit, i) => (
        <li
          key={hit.id}
          className="card space-y-2 transition-shadow hover:shadow-md"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2 text-sm text-gray-500">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-600">
                {i + 1}
              </span>
              <FileText className="h-4 w-4 flex-shrink-0 text-gray-400" />
              {hit.document_id ? (
                <Link
                  href={`/documents/${hit.document_id}`}
                  className="truncate font-mono text-gray-700 hover:text-brand-600"
                >
                  {hit.filename || hit.document_id}
                </Link>
              ) : (
                <span className="truncate font-mono">{hit.filename || "—"}</span>
              )}
            </div>
            <span
              className="flex-shrink-0 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700"
              title="Similarity score"
            >
              {formatScore(hit.score)}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-gray-800">
            {hit.content || "(no content)"}
          </p>
          {/* Relevance bar */}
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-brand-500"
              style={{ width: `${Math.round(hit.score * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ol>
  );
}
