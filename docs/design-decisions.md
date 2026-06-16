# Design Decisions

This document records the key architectural and implementation choices made in the Document Intelligence Pipeline, using the ADR (Architecture Decision Record) format.

## Decision 1: Use of Shared Core Utilities

- **Context**: Every project in the showcase portfolio needs boilerplate code for database connections, Redis clients, logging configuration, error handling, and Pydantic settings. Duplicating this across 12 repositories would create a maintenance burden and inconsistency.
- **Options**:
  1. Duplicate utility modules inside each repository.
  2. Implement a shared library (`shared-core`) that all projects install as an editable dependency.
  3. Use a monorepo with a single `pyproject.toml` managing all packages.
- **Choice**: Option 2 — `shared-core` installed via `pip install -e ../shared-core`.
- **Tradeoff**: Single bug-fix location and consistent APIs across all projects. However, the relative path install breaks in isolated CI environments (GitHub Actions) and requires `shared-core` to be checked out alongside every project. A future fix (private PyPI, git submodule, or monorepo checkout) is needed before repos go public.

## Decision 2: Docker Compose for Local Infrastructure

- **Context**: The pipeline requires PostgreSQL (with pgvector extension) and Redis for the Celery broker. Developers need a reproducible way to run these services without polluting their host system.
- **Options**:
  1. Rely on host-installed Postgres and Redis.
  2. Use `docker-compose.yml` to spin up isolated containers.
  3. Use Testcontainers for on-demand infrastructure in tests only.
- **Choice**: Option 2 — Docker Compose with `pgvector/pgvector:pg16` and `redis:7-alpine`.
- **Tradeoff**: High reproducibility, zero host pollution, instant teardown with `make docker-down`. Requires Docker Desktop installed. Takes disk space for images and persistent volumes (`pgdata`, `redisdata`).

## Decision 3: Linear Pipeline Architecture over DAG-Based Processing

- **Context**: Document processing involves multiple sequential stages: parsing, cleaning, chunking, embedding, and export. The stages could be organized as a linear chain, a directed acyclic graph (DAG), or an event-driven system.
- **Options**:
  1. DAG-based workflow engine (like Airflow or the sibling `async-workflow-engine` project) where each stage is a node with explicit dependencies.
  2. Event-driven pipeline where each stage publishes to a message queue and downstream stages subscribe.
  3. Simple linear pipeline where stages are called sequentially in code: `parse() → clean() → chunk() → embed() → export()`.
- **Choice**: Option 3 — linear pipeline with direct function calls.
- **Tradeoff**: The linear approach is dramatically simpler to implement, test, and debug. Each stage is a pure function or stateless class, making unit testing trivial. The downside is limited parallelism — you can't process chunks in parallel across an embedding service without additional orchestration. If throughput becomes a bottleneck, individual stages can be wrapped as Celery subtasks using `chain()` or `chord()` without restructuring the core logic.

## Decision 4: JSONL as the Export Format

- **Context**: Processed chunks need to be exported in a format that downstream systems (`rag-evaluation-lab`, `personal-knowledge-base-os`) can consume. The format must support streaming reads, variable-length records, and arbitrary metadata.
- **Options**:
  1. CSV — flat, widely supported, but poor for nested data (embeddings are 1536-element arrays).
  2. Parquet — columnar, efficient for large datasets, but requires `pyarrow` and is overkill for the current scale.
  3. JSONL (JSON Lines) — one JSON object per line, streamable, supports nested structures natively.
  4. SQLite database file — portable, queryable, but adds a dependency and isn't streaming-friendly.
- **Choice**: Option 3 — JSONL via `JSONLExporter`.
- **Tradeoff**: JSONL is human-readable, easy to inspect with `head -n 5 output.jsonl`, and trivially parseable with `json.loads()` per line. It handles embedding vectors as native JSON arrays without escaping issues. The file size is larger than Parquet for the same data, but at the expected scale (thousands to tens of thousands of chunks), this is negligible. JSONL is also the de facto standard for ML pipeline data interchange (OpenAI fine-tuning, LangChain imports).

## Decision 5: Sliding-Window Chunking over Sentence or Semantic Splitting

- **Context**: Text must be split into chunks suitable for embedding and retrieval. Chunk boundaries directly affect retrieval quality — too large and relevant passages are diluted; too small and context is lost. Overlapping chunks help ensure cross-boundary content appears in at least one chunk.
- **Options**:
  1. Fixed-size character splitting — split every N characters regardless of word boundaries.
  2. Sentence-based splitting — use NLP sentence tokenization (spaCy, NLTK) to split on sentence boundaries.
  3. Sliding-window word splitting — split every N words with M-word overlap between consecutive chunks.
  4. Semantic splitting — use an embedding model to detect topic shifts and split on semantic boundaries.
- **Choice**: Option 3 originally — `SlidingWindowChunker` with `chunk_size=200` words, `overlap=50` words.
- **Update (superseded)**: The default chunker is now `Chunker`, a thin adapter over `shared_core.docparse.chunk_text`, defaulting to the **semantic** strategy (sentence-aware packing up to a character budget) with `fixed` and `structural` (heading-aware) strategies also available. `SlidingWindowChunker` is retained for backwards compatibility and the demo.
- **Tradeoff**: Semantic chunking respects sentence boundaries (no mid-sentence splits) without an embedding-model call per split point, since `shared-core` packs by sentence regex rather than embeddings. Word-based sliding windows remain available where deterministic fixed-size windows are preferred.

## Decision 6: Offline-First Embeddings via `shared_core.embeddings`

- **Context**: The pipeline needs vector embeddings per chunk. Real embedding APIs (OpenAI `text-embedding-3-small`, sentence-transformers) are rate-limited, cost money, or require GPUs. Development, tests, and the demo must produce consistent output with **no** API calls, while production should use real embeddings when keyed.
- **Options**:
  1. Call OpenAI directly, even in development.
  2. Re-implement a local mock generator in this repo.
  3. Use `shared_core.embeddings.get_embedding_provider(offline=...)` — a deterministic `HashFallbackProvider` with no key, the real `OpenAIEmbeddingProvider` when `OPENAI_API_KEY` is set.
- **Choice**: Option 3. `EmbeddingGenerator` (`embeddings.py`) is a thin synchronous facade over the shared async providers, selecting offline vs real automatically. `MockEmbeddingGenerator` remains as a backwards-compatible alias for the offline path.
- **Tradeoff**: We do **not** re-mock what `shared-core` provides, keeping one embedding implementation across the workspace. The offline vectors are deterministic and stable for tests but lexical rather than semantic — real retrieval quality requires a key. The sync facade runs the async provider via `asyncio`, with a thread-offload guard so it works even inside a running event loop (the FastAPI request path).

## Decision 8: Adopt `shared_core.docparse` for Parsing/Chunking/Dedup

- **Context**: The original repo had local parsers (`if/elif` dispatch, naive HTML/Markdown), a local chunker, and no dedup. `shared-core` (v1.3.0) ships a complete ingestion layer: `get_parser` (PDF/DOCX/HTML/Markdown with dynamically imported heavy deps), `chunk_text` (fixed/semantic/structural), and SHA-256 dedup (`compute_hash`, `filter_duplicates`).
- **Choice**: Replace the local implementations with thin adapters over `shared_core.docparse`. `DocumentParser` resolves a shared parser and normalises missing-optional-dependency / unsupported-format errors into a single `ParseError`. `Chunker` wraps `chunk_text`; `dedup.py` wraps the dedup helpers.
- **Tradeoff**: Far less bespoke code to maintain, real PDF/DOCX/HTML parsing for free, and a uniform `ParsedDocument` (text + title + metadata + page count) that powers metadata extraction. The cost is a hard dependency on `shared-core[docparse]` for the heavy formats — without it, PDF/DOCX raise a clean `ParseError` and are quarantined rather than crashing.

## Decision 9: DB Persistence by Default with In-Memory Fallback (`db_available` probe)

- **Context**: The showcase must run and be **fully tested with no database**, yet demonstrate real persistence. The migrated sibling services established a `db_available` probe pattern.
- **Choice**: `db.py` probes the database on startup (`SELECT 1`, create tables) and `build_store()` returns a `DatabaseDocumentStore` (PostgreSQL) or `InMemoryDocumentStore`. Both implement the same interface, so `DocumentPipeline`, the API, and the worker are backend-agnostic. The vector store mirrors this (pgvector vs `InMemoryVectorStore`). Alembic provides migrations.
- **Tradeoff**: Tests and the demo run instantly with zero infrastructure; production gets durable, queryable storage by setting `DATABASE_URL`. Chunk embeddings are stored as JSON (not a native `pgvector` column) in the relational table so the schema is SQLite-testable; semantic search uses the dedicated vector store instead.

## Decision 10: Error Quarantine over Fail-Fast

- **Context**: A bad file in a batch (unsupported format, missing parser dependency, corrupt bytes) must not abort the whole batch, and operators need to see and retry failures.
- **Choice**: `DocumentPipeline.ingest` never raises — failures are recorded in a quarantine (with the original bytes, base64-encoded), surfaced via `GET /quarantine`, and reprocessable via `POST /quarantine/{id}/reprocess`.
- **Tradeoff**: Resilient batch ingestion and a clear operator workflow, at the cost of storing failed file bytes (bounded by retention policy — see roadmap).

## Decision 11: Heuristic Entity Extraction over spaCy NER

- **Context**: Entity extraction (emails, URLs, names) is a showcase feature, but a trained NER model (spaCy) is a heavy dependency and slow to load — at odds with offline-first, fast tests.
- **Choice**: `entities.py` uses regex + heuristics: emails, URLs (trailing-punctuation-trimmed), phone shapes, and capitalised n-grams (1–3 tokens, stopword-filtered) as a proper-noun proxy.
- **Tradeoff**: Zero heavy dependencies, instant, deterministic, good enough to demonstrate the capability and feed a dashboard. It produces false positives on capitalised phrases and misses lowercase entities — a trained NER model is the documented Phase 4 upgrade.

## Decision 7: Format-Specific Parser Dispatch over Plugin Architecture

- **Context**: The pipeline must handle multiple file formats (txt, md, html, and eventually pdf, docx). Each format requires different extraction logic. The parser needs to route files to the correct handler.
- **Options**:
  1. Plugin/registry architecture — parsers register themselves via decorators or entry points; new formats are added without touching the dispatcher.
  2. Strategy pattern — pass a parser implementation at runtime based on configuration.
  3. Simple dispatch — `if/elif` chain in `DocumentParser.parse_file()` based on file extension.
- **Choice (superseded)**: Originally a direct `if/elif` dispatch. Now dispatch is delegated to `shared_core.docparse.get_parser`, which resolves a parser by extension/MIME from a registered tuple of `BaseParser` subclasses. `DocumentParser` is a thin adapter that calls it and normalises errors.
- **Tradeoff**: We get a maintained, extensible parser registry (PDF/DOCX/HTML/Markdown) for free, with heavy deps dynamically imported. Adding a format is a `shared-core` concern, not a per-project one — eliminating duplicated parsing logic across the workspace.
