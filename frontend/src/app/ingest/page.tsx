"use client";

import { useState, type FormEvent } from "react";
import { FileUp, Loader2, Type, Upload } from "lucide-react";
import IngestResultCard from "@/components/IngestResultCard";
import ErrorMessage from "@/components/ErrorMessage";
import { apiClient } from "@/lib/api";
import type { IngestResult } from "@/types";

type Mode = "text" | "file";

const SAMPLE_TEXT = `# Release Notes — v2.4

We shipped semantic chunking and pgvector-backed similarity search.
Contact support@example.com for migration help.

Highlights:
- 41% lower hallucination rate on the internal benchmark
- New JSONL export for RAG ingestion
`;

export default function IngestPage() {
  const [mode, setMode] = useState<Mode>("text");
  const [filename, setFilename] = useState("notes.md");
  const [text, setText] = useState(SAMPLE_TEXT);
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      let res: IngestResult;
      if (mode === "file") {
        if (!file) {
          setError("Choose a file to ingest.");
          setSubmitting(false);
          return;
        }
        res = await apiClient.ingestFile(file);
      } else {
        if (!text.trim()) {
          setError("Enter some text to ingest.");
          setSubmitting(false);
          return;
        }
        res = await apiClient.ingestText(filename || "document.txt", text);
      }
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Ingest</h1>
        <p className="mt-1 text-sm text-gray-500">
          Run the pipeline on a single document. Files post to{" "}
          <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">/ingest</code>;
          pasted text posts to{" "}
          <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">
            /ingest/text
          </code>
          .
        </p>
      </header>

      <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
        <ModeButton
          active={mode === "text"}
          onClick={() => setMode("text")}
          icon={Type}
          label="Paste text"
        />
        <ModeButton
          active={mode === "file"}
          onClick={() => setMode("file")}
          icon={FileUp}
          label="Upload file"
        />
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        {mode === "text" ? (
          <>
            <div>
              <label
                htmlFor="filename"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Filename
              </label>
              <input
                id="filename"
                className="input"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="document.txt"
              />
            </div>
            <div>
              <label
                htmlFor="text"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Document text
              </label>
              <textarea
                id="text"
                className="input min-h-[220px] font-mono text-xs leading-relaxed"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste markdown, HTML, or plain text…"
              />
            </div>
          </>
        ) : (
          <div>
            <label
              htmlFor="file"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              File
            </label>
            <label
              htmlFor="file"
              className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 px-6 py-10 text-center transition hover:border-brand-400 hover:bg-brand-50/40"
            >
              <Upload className="h-8 w-8 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                {file ? file.name : "Click to choose a file"}
              </span>
              <span className="text-xs text-gray-400">
                PDF, DOCX, HTML, Markdown, or plain text
              </span>
              <input
                id="file"
                type="file"
                className="sr-only"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>
        )}

        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {submitting ? "Ingesting…" : "Ingest document"}
          </button>
        </div>
      </form>

      {error && <ErrorMessage message={error} />}
      {result && <IngestResultCard result={result} />}
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Type;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-brand-600 text-white"
          : "text-gray-600 hover:bg-gray-100"
      }`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}
