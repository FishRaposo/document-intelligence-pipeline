# Failure Modes & Mitigation

Operational failures specific to the Document Intelligence Pipeline, how they manifest, and how they are handled. Items marked **[implemented]** are mitigated in the current code; **[future]** are roadmap items.

## Summary Matrix

| # | Failure | Detection | Status |
|---|---------|-----------|--------|
| 1 | Database connectivity loss | `/health` → `degraded` | **[implemented]** in-memory fallback |
| 2 | Worker / broker unavailable | task never starts | **[implemented]** sync path always works |
| 3 | Unsupported format / missing parser dep | quarantine entry | **[implemented]** quarantine |
| 4 | Corrupt / undecodable bytes | quarantine entry | **[implemented]** quarantine |
| 5 | Duplicate document | `status: duplicate` | **[implemented]** content-hash dedup |
| 6 | Empty / tiny document | `total_chunks: 0` | **[implemented]** safe empty handling |
| 7 | Real embedding API failure | per-chunk empty vector + log | **[implemented]** graceful degrade |
| 8 | Large-file memory pressure | OOM | **[future]** size cap |
| 9 | Quarantine storage growth | table size | **[future]** retention policy |

## 1. Database Connectivity Failure — [implemented]

- **Cause**: PostgreSQL down, network partition, or pool exhaustion.
- **Impact**: `GET /health` reports `degraded` (`database: offline`). The API stays fully functional using the in-memory document + vector stores.
- **Detection**: `/health` payload; SQLAlchemy connection errors in logs.
- **Mitigation**: The `db_available` probe (`db.py`) catches connection failures on startup and falls back to `InMemoryDocumentStore` + `InMemoryVectorStore`. `DatabaseManager` uses `pool_pre_ping=True`. `check_health` wraps the probe so a DB outage never crashes the API.
- **Tradeoff**: In-memory state is per-process and lost on restart — acceptable for the offline/demo mode; durable storage requires a reachable `DATABASE_URL`.

## 2. Worker / Broker Unavailable — [implemented]

- **Cause**: Redis/Celery broker down, or no worker running.
- **Impact**: `POST /ingest/batch` with `async_mode: true` cannot dispatch.
- **Mitigation**: `worker.py` imports with **no** broker (Celery connects lazily). The **synchronous** batch path (`async_mode: false`, the default) runs the full pipeline in-process and never touches the broker, so ingestion always works. The worker's pure logic (`_process_one`, `_process_batch`) is unit-tested without Celery.
- **Future**: dead-letter queue for repeatedly failing async tasks; `task_time_limit` already configured by `shared_core.tasks`.

## 3. Unsupported Format / Missing Parser Dependency — [implemented]

- **Cause**: A file with an unsupported extension, or a PDF/DOCX/HTML when the `shared-core[docparse]` heavy dependency (PyMuPDF / python-docx / beautifulsoup4) is not installed.
- **Impact**: No crash. `DocumentParser` raises a single `ParseError`; the pipeline records a **quarantine** entry with the file bytes and reason.
- **Detection**: `GET /quarantine` lists the entry; the ingest response returns `{status: "quarantined", quarantine_id}`.
- **Recovery**: install the missing extra, then `POST /quarantine/{id}/reprocess`.

## 4. Corrupt / Undecodable Bytes — [implemented]

- **Cause**: Binary content, truncated files, or a parser raising on malformed input.
- **Impact**: Caught by `DocumentPipeline.ingest` (parse errors and any unexpected exception) → quarantined, not a 500. Markdown/text decode uses `errors="replace"` in `shared-core`, so encoding issues degrade gracefully rather than throwing.
- **Detection**: quarantine entry with the failure reason.

## 5. Duplicate Document — [implemented]

- **Cause**: The same content ingested again (possibly under a different filename).
- **Impact**: Detected by SHA-256 over the cleaned text (`compute_hash`). The store's unique `content_hash` plus a pre-insert lookup means the document is **not** re-processed; ingest returns `{status: "duplicate", document_id}` pointing at the existing record. Chunk-level duplicates are dropped via `filter_duplicates` before embedding.
- **Benefit**: no wasted parsing/embedding work; stable document identity.

## 6. Empty / Tiny Document — [implemented]

- **Cause**: Empty upload or whitespace-only content after cleaning.
- **Impact**: `chunk_text("")` returns `[]`; the document is stored with `total_chunks: 0` and no vectors indexed. No crash, no infinite loop (`Chunker`/`SlidingWindowChunker` validate `overlap < chunk_size`).
- **Detection**: `total_chunks: 0` in the response.

## 7. Real Embedding API Failure — [implemented]

- **Cause**: With `OPENAI_API_KEY` set, the OpenAI embeddings call may rate-limit, time out, or fail.
- **Impact**: `EmbeddingGenerator.embed_chunks` catches per-chunk failures, logs a warning, and sets that chunk's embedding to `[]` (it simply won't be indexed for search) — the rest of the document still ingests.
- **Detection**: warning logs; chunks with empty embeddings absent from search results.
- **Future**: exponential-backoff retry and request batching for the OpenAI path.

## 8. Large-File Memory Pressure — [future]

- **Cause**: `POST /ingest` reads the whole upload into memory.
- **Impact**: very large files (hundreds of MB) can exhaust RAM.
- **Future**: a `max_upload_size` config + early 413 rejection; stream to a temp file and parse from disk.

## 9. Quarantine / Storage Growth — [future]

- **Cause**: quarantine retains failed file bytes (base64) for reprocessing; high failure volume grows the table.
- **Future**: a retention policy (TTL / size cap) and an option to store only a reference rather than the bytes.
