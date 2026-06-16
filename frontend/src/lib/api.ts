// Typed API client for the Document Intelligence Pipeline backend.
//
// Strategy: every method attempts the LIVE FastAPI endpoint first. If the fetch
// fails (network error, backend down, non-OK status), it transparently falls
// back to the bundled mock dataset so the whole UI stays explorable offline.
// When any call falls back, a module-level flag flips so the UI can surface a
// visible "Demo mode" indicator.

import type {
  Chunk,
  ChunkListResponse,
  DocumentDetail,
  DocumentListResponse,
  DocumentSummary,
  HealthCheck,
  IngestResult,
  QuarantineEntry,
  QuarantineListResponse,
  SearchHit,
  SearchResponse,
} from "@/types";
import {
  mockChunks,
  mockDocument,
  mockDocuments,
  mockIngest,
  mockQuarantine,
  mockSearch,
} from "@/lib/mockData";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type DemoListener = (demo: boolean) => void;

class DemoState {
  private demo = false;
  private listeners = new Set<DemoListener>();

  get active(): boolean {
    return this.demo;
  }

  set(value: boolean): void {
    if (this.demo === value) return;
    this.demo = value;
    this.listeners.forEach((l) => l(value));
  }

  subscribe(listener: DemoListener): () => void {
    this.listeners.add(listener);
    listener(this.demo);
    return () => this.listeners.delete(listener);
  }
}

export const demoState = new DemoState();

class ApiClient {
  constructor(private baseUrl: string) {}

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  /** Run a live call; on any failure, record demo mode and return the fallback. */
  private async withFallback<T>(
    live: () => Promise<T>,
    fallback: () => T
  ): Promise<T> {
    try {
      const result = await live();
      demoState.set(false);
      return result;
    } catch {
      demoState.set(true);
      return fallback();
    }
  }

  // -- Browsing --------------------------------------------------------------
  async listDocuments(): Promise<DocumentSummary[]> {
    return this.withFallback(
      async () => {
        const data = await this.request<DocumentListResponse>("/documents");
        return data.documents;
      },
      () => mockDocuments()
    );
  }

  async getDocument(id: string): Promise<DocumentDetail> {
    return this.withFallback(
      () => this.request<DocumentDetail>(`/documents/${encodeURIComponent(id)}`),
      () => {
        const doc = mockDocument(id);
        if (!doc) throw new Error(`Document '${id}' not found`);
        return doc;
      }
    );
  }

  async getChunks(id: string): Promise<Chunk[]> {
    return this.withFallback(
      async () => {
        const data = await this.request<ChunkListResponse>(
          `/documents/${encodeURIComponent(id)}/chunks`
        );
        return data.chunks;
      },
      () => {
        const chunks = mockChunks(id);
        if (!chunks) throw new Error(`Document '${id}' not found`);
        return chunks;
      }
    );
  }

  // -- Ingestion -------------------------------------------------------------
  async ingestText(filename: string, text: string): Promise<IngestResult> {
    return this.withFallback(
      () =>
        this.request<IngestResult>("/ingest/text", {
          method: "POST",
          body: JSON.stringify({ filename, text }),
        }),
      () => mockIngest(filename, text)
    );
  }

  async ingestFile(file: File): Promise<IngestResult> {
    return this.withFallback(
      async () => {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(`${this.baseUrl}/ingest`, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          const error = await response
            .json()
            .catch(() => ({ detail: response.statusText }));
          throw new Error(error.detail || `Upload failed: ${response.status}`);
        }
        return response.json();
      },
      () => mockIngest(file.name, "(file contents processed by the backend)")
    );
  }

  // -- Search ----------------------------------------------------------------
  async search(query: string, topK = 5): Promise<SearchHit[]> {
    return this.withFallback(
      async () => {
        const data = await this.request<SearchResponse>("/search", {
          method: "POST",
          body: JSON.stringify({ query, top_k: topK }),
        });
        return data.results;
      },
      () => mockSearch(query, topK)
    );
  }

  // -- Quarantine ------------------------------------------------------------
  async listQuarantine(): Promise<QuarantineEntry[]> {
    return this.withFallback(
      async () => {
        const data = await this.request<QuarantineListResponse>("/quarantine");
        return data.quarantine;
      },
      () => mockQuarantine()
    );
  }

  async reprocessQuarantine(entryId: string): Promise<IngestResult> {
    return this.withFallback(
      () =>
        this.request<IngestResult>(
          `/quarantine/${encodeURIComponent(entryId)}/reprocess`,
          { method: "POST" }
        ),
      () => ({
        status: "completed",
        filename: "reprocessed.txt",
        document_id: `doc-demo-${entryId}`,
        total_chunks: 1,
        title: "Reprocessed (demo)",
        metadata: {},
        entities: { emails: [], urls: [], phones: [], capitalised: [] },
        chunks: [],
        error: null,
        quarantine_id: null,
      })
    );
  }

  // -- Health ----------------------------------------------------------------
  async health(): Promise<HealthCheck> {
    return this.withFallback(
      () => this.request<HealthCheck>("/health"),
      () => ({
        service: "document-intelligence-pipeline",
        status: "demo",
        dependencies: { database: "offline", redis: "offline" },
      })
    );
  }

  /** URL for the JSONL export of a document (live backend only). */
  exportUrl(docId: string): string {
    return `${this.baseUrl}/export/${encodeURIComponent(docId)}`;
  }
}

export const apiClient = new ApiClient(API_BASE);
