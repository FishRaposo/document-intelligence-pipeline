# Execution Plan — Document Intelligence Pipeline

What was built to take this project from a ~70-80% skeleton to a fully-implemented, tested, documented MVP, and what remains.

## Starting Point

The repo had working-but-shallow stages: local naive parsers, a word-window chunker, a deterministic mock embedder, a JSONL exporter not wired into the API, a placeholder Celery task, ORM models using a hard `pgvector` column (Postgres-only), and a handful of tests. The `/ingest` endpoint bypassed the parser and did a raw UTF-8 decode. No dedup, metadata, entities, quarantine, search, or persistence wiring.

## What Was Built

### Core modules rewritten onto `shared-core`
- **`parsers.py`** — thin adapter over `shared_core.docparse.get_parser`; returns the uniform `ParsedDocument`; normalises unsupported-format and missing-optional-dependency errors into one `ParseError`.
- **`chunkers.py`** — `Chunker` over `shared_core.docparse.chunk_text` (fixed/semantic/structural); legacy `SlidingWindowChunker` retained.
- **`embeddings.py`** — `EmbeddingGenerator`, a sync facade over `shared_core.embeddings.get_embedding_provider` (offline `HashFallbackProvider` default; real OpenAI when keyed). Robust to running event loops. `MockEmbeddingGenerator` kept as an offline alias.
- **`dedup.py`** — `content_hash` + `dedup_chunks` over `compute_hash` / `filter_duplicates`.

### New domain modules
- **`metadata.py`** — `extract_metadata` (title, author, dates, word/char/page counts).
- **`entities.py`** — `extract_entities` (emails, URLs, phones, capitalised n-grams; regex/heuristic, no spaCy).
- **`pipeline.py`** — `DocumentPipeline` orchestrating parse → clean → metadata + entities → chunk → dedup → embed → persist → index, with quarantine-on-failure, `search`, and `reprocess_quarantine`.
- **`storage.py`** — `InMemoryDocumentStore` (offline default).
- **`storage_db.py`** — `DatabaseDocumentStore` (rewritten) mirroring the same interface.
- **`db.py`** — `check_db()` / `build_store()` implementing the `db_available` probe + in-memory fallback.

### Persistence
- **`models.py`** — `Document` (+ `content_hash` unique, title/author/word_count/metadata/entities), `Chunk` (+ content_hash, JSON embedding), new `ProcessingJob` and `QuarantineEntry`. Embeddings stored as JSON so the schema is SQLite-testable.
- **Alembic** — initial migration `7b986bbaa911_initial_schema.py` generated for all four tables; `env.py` registers the models.

### Worker
- **`worker.py`** — real `process_document_task` and `batch_ingest_task` built on `shared_core.tasks.create_celery_app`; pure `_process_one` / `_process_batch` helpers for testability; importable with no broker.

### API (`main.py`)
- Rewritten with a lifespan DB probe and these endpoints: `POST /ingest` (file), `POST /ingest/text`, `POST /ingest/batch` (sync or async→worker), `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/chunks`, `POST /search`, `GET /quarantine`, `POST /quarantine/{id}/reprocess`, `GET /export/{id}`, `GET /health`. Wires `RequestLoggingMiddleware` and the shared error handler.

### Exporter
- **`exporters.py`** — `JSONLExporter.dumps` (for HTTP) + `to_rag_records` (RAG-ready `{id, text, metadata}`).

### Tests (offline; `shared_core.testing.MockDatabase`, no network)
- `test_parsers` (incl. PDF/DOCX behind `importorskip`), `test_chunkers`, `test_embeddings`, `test_metadata`, `test_entities`, `test_dedup`, `test_exporters`, `test_models`, `test_storage` (parametrised in-memory + SQLite), `test_pipeline` (integration: ingest/dedup/quarantine/search), `test_persistence` (DB path), `test_worker`, `test_api` (every endpoint, success + error), `test_core` (demo smoke).

### Demo & docs
- `examples/run_demo.py` rewritten to showcase the full pipeline (completed/duplicate/quarantined, entities, search, JSONL) — exits 0.
- README rewritten to the full standard (Mermaid architecture). `docs/{architecture,design-decisions,failure-modes,roadmap,security}.md` rewritten/expanded to the implemented reality. This `EXECUTION_PLAN.md` added. `AGENTS.md` updated.
- Spine updated: `requirements.txt` (+python-multipart), `pyproject.toml` (deps + `[dev]`, src layout), `Makefile` (worker/migrate targets already present).

## Verification

- `ruff format` + `ruff check` on `src/doc_pipeline tests examples` — clean.
- `pytest` — full suite passes offline (no DB, no keys).
- `examples/run_demo.py` — exits 0.

## What's Next

See [roadmap.md](roadmap.md) Phase 3+: webhook callbacks, chunk-preview highlighting, a metrics/throughput endpoint, a job-status endpoint, upload size caps, PII redaction, trained NER, and OCR.
