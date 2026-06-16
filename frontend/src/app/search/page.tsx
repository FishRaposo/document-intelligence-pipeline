"use client";

import { useState, type FormEvent } from "react";
import { Loader2, Search, SearchX } from "lucide-react";
import SearchResults from "@/components/SearchResults";
import EmptyState from "@/components/EmptyState";
import ErrorMessage from "@/components/ErrorMessage";
import { CardSkeleton } from "@/components/LoadingSkeleton";
import { apiClient } from "@/lib/api";
import type { SearchHit } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const results = await apiClient.search(query.trim(), topK);
      setHits(results);
      setLastQuery(query.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Similarity search
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Embeds your query and returns the most similar stored chunks via{" "}
          <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">/search</code>.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="card flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. qubits superposition entanglement"
            aria-label="Search query"
          />
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="topk" className="text-xs text-gray-500">
            Top K
          </label>
          <select
            id="topk"
            className="input w-20"
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          >
            {[3, 5, 10, 20].map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </div>
      </form>

      {error && <ErrorMessage message={error} />}

      {loading ? (
        <div className="space-y-3">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : hits === null ? (
        <EmptyState
          icon={Search}
          title="Search the corpus"
          description="Enter a query to retrieve the most relevant chunks ranked by similarity score."
        />
      ) : hits.length === 0 ? (
        <EmptyState
          icon={SearchX}
          title="No matches"
          description={`Nothing matched "${lastQuery}". Try a broader query.`}
        />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            {hits.length} {hits.length === 1 ? "result" : "results"} for{" "}
            <span className="font-medium text-gray-900">“{lastQuery}”</span>
          </p>
          <SearchResults hits={hits} />
        </div>
      )}
    </div>
  );
}
