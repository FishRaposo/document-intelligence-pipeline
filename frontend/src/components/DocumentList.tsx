import Link from "next/link";
import { ChevronRight, FileText } from "lucide-react";
import { FormatBadge } from "@/components/StatusBadge";
import { formatDate } from "@/lib/format";
import type { DocumentSummary } from "@/types";

export default function DocumentList({
  documents,
}: {
  documents: DocumentSummary[];
}) {
  return (
    <ul className="space-y-3" data-testid="document-list">
      {documents.map((doc) => (
        <li key={doc.id}>
          <Link
            href={`/documents/${doc.id}`}
            className="card flex items-center gap-4 transition-shadow hover:shadow-md"
          >
            <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <FileText className="h-5 w-5" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="truncate font-semibold text-gray-900">
                  {doc.title || doc.filename}
                </h3>
                <FormatBadge format={doc.format} />
              </div>
              <p className="mt-0.5 truncate text-sm text-gray-500">
                {doc.filename}
                {doc.author ? ` · ${doc.author}` : ""} · {formatDate(doc.created_at)}
              </p>
            </div>
            <div className="hidden flex-shrink-0 text-right sm:block">
              <div className="text-sm font-semibold text-gray-900">
                {doc.total_chunks} chunks
              </div>
              <div className="text-xs text-gray-400">
                {doc.word_count.toLocaleString()} words
              </div>
            </div>
            <ChevronRight className="h-5 w-5 flex-shrink-0 text-gray-300" />
          </Link>
        </li>
      ))}
    </ul>
  );
}
