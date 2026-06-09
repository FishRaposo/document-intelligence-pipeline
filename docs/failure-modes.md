# Failure Modes & Mitigation

This document catalogues operational failures specific to the Document Intelligence Pipeline, how they manifest, and strategies for detection and recovery.

## 1. Database Connectivity Failure

- **Cause**: PostgreSQL container down, network partition, or connection pool exhaustion from high-concurrency ingestion.
- **Impact**: Health check (`GET /health`) reports `degraded` status with `database: offline`. In the planned schema, document and chunk persistence fail. The API remains up for stateless operations but cannot track processing status.
- **Detection**: `/health` endpoint returns `{"status": "degraded", "dependencies": {"database": "offline"}}`. SQLAlchemy connection timeouts appear in logs.
- **Mitigation**: `DatabaseManager` uses SQLAlchemy connection pooling. The health check wraps the database probe in a try/except so a database failure doesn't crash the entire API. Docker Compose includes a `pg_isready` healthcheck with 5-second interval and 5 retries.
- **Future Fix**: Add `pool_pre_ping=True` to the SQLAlchemy engine for automatic stale connection detection. Configure Docker Compose restart policies (`restart: unless-stopped`). Add connection pool metrics to detect exhaustion before it becomes critical.

## 2. Queue Backlog / Worker Starvation

- **Cause**: Large batch of documents submitted for ingestion, slow embedding API calls, or Celery worker process crash during document processing.
- **Impact**: Tasks accumulate in the Redis queue in `PENDING` state. Processing latency increases. If Redis memory fills up, new tasks are rejected.
- **Detection**: Redis `LLEN` on the Celery queue key. Celery worker heartbeat monitoring. Processing time exceeding expected thresholds.
- **Mitigation**: Celery is configured with JSON serialization and UTC timezone. Redis 7 runs with persistent storage (`redisdata` volume) to survive container restarts without losing queued tasks.
- **Future Fix**: Add Celery `task_time_limit` and `task_soft_time_limit` to prevent individual tasks from blocking workers indefinitely. Implement autoscaling with `celery worker --autoscale=10,3`. Add Redis memory limits and eviction policies. Build a dead-letter queue for repeatedly failing tasks.

## 3. Malformed or Corrupt File Upload

- **Cause**: User uploads a binary file (actual PDF, image, executable) to the `POST /ingest` endpoint, which decodes raw bytes as UTF-8 via `contents.decode("utf-8")`.
- **Impact**: `UnicodeDecodeError` exception raised, resulting in an unhandled 500 error. No structured error response — the client gets a raw exception trace (in debug mode) or a generic error.
- **Detection**: 500 error responses on `/ingest`. Exception logs containing `UnicodeDecodeError` or `codec can't decode byte`.
- **Mitigation**: Currently none. The endpoint assumes all uploads are valid UTF-8 text.
- **Future Fix**: Add content-type detection using `python-magic` or the file extension. Validate the `Content-Type` header from the upload. Wrap the decode in a try/except with a proper `ParseError` that returns a 422 response. Route binary formats (PDF, DOCX) to their respective parsers instead of attempting UTF-8 decode.

## 4. Unsupported File Format

- **Cause**: `DocumentParser.parse_file()` receives a file with an extension not in the supported set (`.txt`, `.md`, `.html`). PDF and DOCX are specifically called out in the project goals but are not yet implemented.
- **Impact**: `ValueError("Unsupported extension: .pdf")` raised. Since `ValueError` is not a `BaseApplicationError`, it bypasses the structured error handler and results in a raw 500 response.
- **Detection**: 500 errors when processing PDF or DOCX files. Exception logs containing `Unsupported extension`.
- **Mitigation**: The parser explicitly checks the extension before attempting to read, so it fails fast rather than producing garbage output.
- **Future Fix**: Create a `ParseError(BaseApplicationError)` exception class with a 422 status code. Add PDF parsing via `pdfplumber` or `pymupdf`. Add DOCX parsing via `python-docx`. Implement an error quarantine system that logs unsupported files with their metadata for later manual review or re-processing when support is added.

## 5. Encoding and Character Set Issues

- **Cause**: Source documents encoded in non-UTF-8 character sets (Latin-1, Windows-1252, Shift-JIS) are read with `encoding="utf-8"` in `DocumentParser._parse_text()`, `_parse_markdown()`, and `_parse_html()`.
- **Impact**: `UnicodeDecodeError` during file parsing. Documents with mixed encoding (e.g., UTF-8 with embedded Latin-1 characters from copy-paste) produce mojibake — garbled text that chunks and embeds incorrectly without raising an error.
- **Detection**: `UnicodeDecodeError` in parser logs. Downstream retrieval returning nonsensical chunk text. Manual inspection of JSONL output revealing garbled characters (e.g., `Ã©` instead of `é`).
- **Mitigation**: Currently none. All file reads use `encoding="utf-8"` hardcoded.
- **Future Fix**: Add encoding detection using `chardet` or `charset-normalizer` as a pre-parsing step. Implement a two-pass strategy: attempt UTF-8 first, fall back to detected encoding. Log a warning when non-UTF-8 encoding is detected. Store the detected encoding in document metadata for traceability.

## 6. Chunker Edge Cases

- **Cause**: `SlidingWindowChunker` uses word-based splitting (`text.split()`) with configurable `chunk_size` and `overlap`. Edge cases arise with:
  - Very short documents (fewer words than `chunk_size`) — produces a single chunk, the early `break` condition triggers
  - Empty or whitespace-only text (after cleaning) — `words` list is empty, returns empty `chunks` list
  - `overlap >= chunk_size` — produces an infinite loop (`idx` never advances or goes negative)
  - Very long single words (URLs, base64 strings) — a single "word" can be thousands of characters, producing chunks that exceed embedding model token limits
- **Impact**: Empty chunks list causes downstream stages to produce empty JSONL exports. Infinite loop hangs the worker or API request. Oversized chunks may be silently truncated by the embedding API, losing information.
- **Detection**: Empty response from `/ingest` with `total_chunks: 0`. Request timeout on the API. Embedding API returning truncation warnings.
- **Mitigation**: The `break` condition (`len(chunk_words) < self.chunk_size`) handles short documents correctly. Empty text produces an empty list (safe, but should be flagged).
- **Future Fix**: Add input validation in `SlidingWindowChunker.__init__()` to enforce `0 < overlap < chunk_size`. Add a minimum content length check before chunking. Implement character-level length limits per chunk in addition to word count. Log warnings for edge cases (empty input, single-chunk output).

## 7. Embedding API Failures (Future)

- **Cause**: When `MockEmbeddingGenerator` is replaced with a real embedding service (OpenAI API or local sentence-transformers), failures include: rate limiting (429 errors), network timeouts, API key expiration, model deprecation, or response format changes.
- **Impact**: Chunks are created but lack embeddings. Without embeddings, chunks cannot be used for vector similarity search, breaking the RAG pipeline. Partial failures leave some chunks embedded and others not, creating inconsistent state.
- **Detection**: Non-200 responses from the embedding API. `openai.RateLimitError` or `httpx.TimeoutException` in logs. Chunks in database with `NULL` embedding vectors.
- **Mitigation**: Not applicable in current mock state. `MockEmbeddingGenerator` never fails — it's a pure computation.
- **Future Fix**: Implement exponential backoff with retry (3 attempts, 1s/2s/4s delays) for transient API errors. Batch embedding requests (up to 2048 texts per call for OpenAI) to minimize API round-trips. Add a fallback to a local model if the API is unavailable. Track embedding status per chunk in the database to enable re-embedding of failed chunks without re-processing the entire document.

## 8. JSONL Export Disk Failures

- **Cause**: `JSONLExporter.export()` opens a file at `output_path` for writing. Failures include: disk full, permission denied, path traversal creating unexpected files, or concurrent writes to the same output file from parallel workers.
- **Impact**: `IOError` or `PermissionError` raised during export. Partial JSONL files with incomplete JSON on the last line. Concurrent writes produce interleaved JSON lines, creating corrupt output.
- **Detection**: Exception logs during export. Truncated or malformed JSONL files. `json.loads()` failing on downstream consumers.
- **Mitigation**: Currently none. `JSONLExporter` opens the file in write mode (`"w"`), overwriting any existing content.
- **Future Fix**: Write to a temporary file first, then atomically rename to the target path (`os.replace()`). Use file locking (`fcntl.flock` on Linux) for concurrent access. Validate available disk space before starting export. Add checksum verification (SHA-256 of the complete file) as a final step.

## 9. Large File Memory Exhaustion

- **Cause**: The `POST /ingest` endpoint calls `await file.read()`, loading the entire uploaded file into memory. For very large files (hundreds of MB or GB), this can exhaust available RAM.
- **Impact**: `MemoryError` or OOM kill by the OS. The FastAPI worker process crashes, dropping all in-flight requests. If running with multiple Uvicorn workers, other workers are unaffected.
- **Detection**: Process killed with signal 9 (OOM). Sudden 502/503 errors from a reverse proxy. System memory monitoring alerts.
- **Mitigation**: Currently none. No file size limit is enforced on uploads.
- **Future Fix**: Add a `max_upload_size` configuration parameter (e.g., 50 MB). Use streaming reads with `file.read(chunk_size)` instead of loading the entire file. For very large documents, write the upload to a temporary file first, then process it with the file-based `DocumentParser.parse_file()` method. Add FastAPI middleware to reject oversized requests early with a 413 response.
