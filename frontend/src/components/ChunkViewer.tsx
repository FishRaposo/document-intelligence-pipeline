"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { truncate } from "@/lib/format";
import type { Chunk } from "@/types";

/**
 * Chunk-preview viewer: each chunk shows a one-line preview and expands to the
 * full content on click. The first chunk starts expanded so there is always
 * visible content.
 */
export default function ChunkViewer({ chunks }: { chunks: Chunk[] }) {
  return (
    <ul className="space-y-2" data-testid="chunk-viewer">
      {chunks.map((chunk, i) => (
        <ChunkRow key={chunk.id} chunk={chunk} defaultOpen={i === 0} />
      ))}
    </ul>
  );
}

function ChunkRow({ chunk, defaultOpen }: { chunk: Chunk; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <li className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-gray-50"
        aria-expanded={open}
      >
        {open ? (
          <ChevronDown className="h-4 w-4 flex-shrink-0 text-gray-400" />
        ) : (
          <ChevronRight className="h-4 w-4 flex-shrink-0 text-gray-400" />
        )}
        <span className="flex h-6 w-8 flex-shrink-0 items-center justify-center rounded bg-brand-50 text-xs font-semibold text-brand-700">
          #{chunk.chunk_index}
        </span>
        {!open && (
          <span className="min-w-0 flex-1 truncate text-sm text-gray-600">
            {truncate(chunk.content, 120)}
          </span>
        )}
        <span className="ml-auto flex-shrink-0 text-xs text-gray-400">
          {chunk.word_count} words
        </span>
      </button>
      {open && (
        <div className="border-t border-gray-100 bg-gray-50 px-4 py-3">
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
            {chunk.content}
          </p>
        </div>
      )}
    </li>
  );
}
