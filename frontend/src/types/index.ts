// Type definitions mirroring the Document Intelligence Pipeline FastAPI backend
// (src/doc_pipeline/main.py + storage.py + pipeline.py response shapes).

/** A document summary as returned by GET /documents. */
export interface DocumentSummary {
  id: string;
  filename: string;
  format: string;
  title: string | null;
  author: string | null;
  total_chunks: number;
  word_count: number;
  created_at: string;
}

export interface DocumentListResponse {
  documents: DocumentSummary[];
}

/** Extracted entities (heuristic NER). */
export interface DocumentEntities {
  emails: string[];
  urls: string[];
  phones: string[];
  capitalised: string[];
}

/** Per-document metadata as produced by metadata.extract_metadata. */
export interface DocumentMetadata {
  title?: string | null;
  author?: string | null;
  dates?: string[];
  word_count?: number;
  char_count?: number;
  page_count?: number | null;
  file_size_bytes?: number;
  source_metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

/** Full document detail as returned by GET /documents/{id}. */
export interface DocumentDetail {
  id: string;
  filename: string;
  format: string;
  file_size_bytes: number;
  total_chunks: number;
  content_hash: string;
  title: string | null;
  author: string | null;
  word_count: number;
  entities: DocumentEntities;
  metadata: DocumentMetadata;
  created_at: string;
}

/** A stored chunk as returned by GET /documents/{id}/chunks. */
export interface Chunk {
  id: string;
  chunk_index: number;
  content: string;
  word_count: number;
}

export interface ChunkListResponse {
  document_id: string;
  chunks: Chunk[];
}

/** Outcome of POST /ingest and /ingest/text (IngestResult.to_dict). */
export interface IngestResult {
  status: "completed" | "duplicate" | "quarantined";
  filename: string;
  document_id: string | null;
  total_chunks: number;
  title: string | null;
  metadata: DocumentMetadata;
  entities: DocumentEntities;
  chunks: { chunk_id: number; content: string; word_count: number }[];
  error: string | null;
  quarantine_id: string | null;
}

/** One ranked hit from POST /search. */
export interface SearchHit {
  id: string;
  score: number;
  document_id: string | null;
  filename: string | null;
  chunk_id: string | null;
  content: string | null;
}

export interface SearchResponse {
  query: string;
  results: SearchHit[];
}

export interface SearchRequest {
  query: string;
  top_k?: number;
}

/** A quarantined entry as returned by GET /quarantine (content_b64 stripped). */
export interface QuarantineEntry {
  id: string;
  filename: string;
  format: string | null;
  file_size_bytes: number;
  reason: string;
  created_at: string;
}

export interface QuarantineListResponse {
  quarantine: QuarantineEntry[];
}

/** Health probe as returned by GET /health (shared_core.health.check_health). */
export interface HealthCheck {
  service: string;
  status?: string;
  dependencies?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}
