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
- **Choice**: Option 3 — `SlidingWindowChunker` with `chunk_size=200` words, `overlap=50` words.
- **Tradeoff**: Word-based sliding windows are fast, deterministic, and require no NLP dependencies. The overlap (25% of chunk size) ensures that a sentence spanning a boundary appears in full in at least one chunk. The downside is that chunk boundaries don't respect semantic or paragraph boundaries — a chunk might split mid-sentence. Sentence-based splitting (option 2) is planned as a future alternative. Semantic splitting (option 4) is powerful but requires an embedding model call per potential split point, which is too expensive for the MVP.

## Decision 6: Mock Embedding Generator for Development

- **Context**: The pipeline needs to produce vector embeddings for each chunk. Real embedding APIs (OpenAI `text-embedding-3-small`, sentence-transformers) are either rate-limited, cost money per token, or require GPU resources. During development and testing, the pipeline should produce consistent, reproducible output without external API calls.
- **Options**:
  1. Call OpenAI embeddings API directly, even during development.
  2. Use a local sentence-transformers model (e.g., `all-MiniLM-L6-v2`).
  3. Implement a deterministic mock that generates vectors from character ordinals.
  4. Skip embeddings entirely and add them later.
- **Choice**: Option 3 — `MockEmbeddingGenerator` that computes `sum(ord(c) for c in text[:100]) / 1000.0` and generates a scaled vector.
- **Tradeoff**: Zero external dependencies, deterministic output (same text always produces same vector), instant execution. The vectors have no semantic meaning, so they can't be used for actual similarity search. The generator is designed to be a drop-in replacement: swap `MockEmbeddingGenerator` for `OpenAIEmbeddingGenerator` (same `embed_text()` interface) when real embeddings are needed. The configurable `dimension` parameter (default: 1536) matches OpenAI's `text-embedding-3-small` output dimensions.

## Decision 7: Format-Specific Parser Dispatch over Plugin Architecture

- **Context**: The pipeline must handle multiple file formats (txt, md, html, and eventually pdf, docx). Each format requires different extraction logic. The parser needs to route files to the correct handler.
- **Options**:
  1. Plugin/registry architecture — parsers register themselves via decorators or entry points; new formats are added without touching the dispatcher.
  2. Strategy pattern — pass a parser implementation at runtime based on configuration.
  3. Simple dispatch — `if/elif` chain in `DocumentParser.parse_file()` based on file extension.
- **Choice**: Option 3 — direct `if/elif` dispatch in `DocumentParser.parse_file()` using `os.path.splitext()`.
- **Tradeoff**: The simplest approach for a small, known set of formats. Adding a new format means adding one `elif` branch and one `_parse_*` method — about 5 lines of code. The plugin architecture (option 1) is more extensible but adds significant complexity (metaclasses, registry dicts, dynamic imports) for diminishing returns when the format list is small and static. If the format count grows beyond ~8, refactoring to a registry pattern would be worthwhile.
