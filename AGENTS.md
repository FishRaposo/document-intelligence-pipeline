# AGENTS.md — document-intelligence-pipeline

## What This Is

A multi-stage document ingestion pipeline: parse (txt/md/html/pdf/docx) → clean → extract metadata + entities → chunk → content-hash dedup → embed → persist → index for vector search. Offline-first (runs and is fully tested with no API keys and no database) and real-when-keyed (OpenAI embeddings + PostgreSQL/pgvector when configured). Built on `shared-core` v1.3.0. Feeds `rag-evaluation-lab` and `personal-knowledge-base-os`.

## Commands

```bash
make install          # pip install -e ../shared-core[...]; pip install -e .[dev]
make dev              # python -m doc_pipeline.main (FastAPI on :8000)
make test             # pytest
make lint             # ruff check .
make format           # ruff format .
make typecheck        # pyright src/
make demo             # python examples/run_demo.py (full offline pipeline)
make worker           # celery -A src.doc_pipeline.worker worker --loglevel=info
make migrate          # alembic revision --autogenerate -m "auto"
make upgrade          # alembic upgrade head
make docker-up        # docker compose up -d (Postgres pgvector:pg16 + Redis 7)
make docker-down      # docker compose down
```

Run a single test: `pytest tests/test_pipeline.py -q`.

## Entry Point

`src/doc_pipeline/main.py` — FastAPI app. On startup a `db_available` probe selects PostgreSQL (+ pgvector) or in-memory backends. Endpoints:

- `POST /ingest` — file upload (multipart) → full pipeline.
- `POST /ingest/text` — raw text/md/html string (JSON body).
- `POST /ingest/batch` — sync, or `async_mode: true` → Celery `batch_ingest_task`.
- `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/chunks` — browse.
- `POST /search` — embed query, cosine-rank stored chunks.
- `GET /quarantine`, `POST /quarantine/{id}/reprocess` — failed-file workflow.
- `GET /export/{id}` — RAG-ready JSONL.
- `GET /health` — DB + Redis via `shared_core.health.check_health`.

## Source Modules

```
src/doc_pipeline/
├── main.py        # FastAPI app + all endpoints; startup db probe
├── pipeline.py    # DocumentPipeline orchestrator (+ search, quarantine reprocess)
├── parsers.py     # DocumentParser — adapter over shared_core.docparse.get_parser
├── cleaners.py    # clean_extracted_text()
├── metadata.py    # extract_metadata() — title/author/dates/counts
├── entities.py    # extract_entities() — emails/urls/phones/capitalised n-grams
├── chunkers.py    # Chunker (shared_core chunk_text) + SlidingWindowChunker
├── dedup.py       # content_hash, dedup_chunks (shared_core compute_hash/filter_duplicates)
├── embeddings.py  # EmbeddingGenerator (shared_core embeddings; offline default)
├── exporters.py   # JSONLExporter, to_rag_records
├── storage.py     # InMemoryDocumentStore (offline default)
├── storage_db.py  # DatabaseDocumentStore (PostgreSQL; same interface)
├── db.py          # check_db()/build_store() — db_available probe + fallback
├── models.py      # Document, Chunk, ProcessingJob, QuarantineEntry
├── worker.py      # Celery process_document_task / batch_ingest_task (no broker needed)
├── config.py      # AppConfig(BaseAppConfig)
└── errors.py      # re-exports shared_core.errors.application_error_handler
```

## shared-core Usage (do NOT re-mock these)

`docparse` (get_parser, chunk_text, ChunkStrategy, compute_hash, filter_duplicates, ParsedDocument) · `embeddings` (get_embedding_provider, HashFallbackProvider) · `vectorstore` (get_vector_store, InMemoryVectorStore, VectorRecord) · `database` (DatabaseManager, Base, UUIDMixin, TimestampMixin) · `tasks` (create_celery_app) · `health`, `errors`, `logging`, `config` · `testing` (MockDatabase, MockRedisClient) in tests.

## Persistence

Default PostgreSQL via `db.py`'s probe; transparent in-memory fallback for tests/demo. Tables: `documents`, `chunks`, `processing_jobs`, `quarantine`. Alembic migration in `alembic/versions/`. Chunk embeddings stored as JSON (SQLite-testable); semantic search uses `shared_core.vectorstore` (pgvector with a DB, in-memory otherwise).

## Tests

`tests/` — offline, no network, no real DB (uses `MockDatabase` + offline providers). Covers every core module, the end-to-end flow, persistence (in-memory + SQLite), every API endpoint (success + error), the worker, and a demo smoke test. ~127 tests.

## Docker Services

- **postgres**: `pgvector/pgvector:pg16` on `:5432` — container `dip_postgres`
- **redis**: `redis:7-alpine` on `:6379` — container `dip_redis`

## When to Update This AGENTS.md

- New endpoints, pipeline stages, or `shared-core` modules adopted.
- New ORM models / migrations.
- Worker task changes.
- Changes to the offline-first / db_available behavior.
