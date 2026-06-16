# Document Intelligence Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3+-37814A?logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A multi-stage document ingestion pipeline that turns raw files (PDF, DOCX, HTML, Markdown, text) into clean, deduplicated, semantically chunked, vector-embedded, RAG-ready knowledge — with metadata + entity extraction, an error quarantine, similarity search, and JSONL export.**

## Why This Exists

Every RAG system, knowledge base, and AI agent depends on the same unglamorous upstream work: turning messy, heterogeneous documents into clean, chunked, embedded data. Most teams cobble this together as a one-off script buried inside their retrieval codebase. That approach breaks the moment you need a second file format, want to skip re-ingesting a file you already processed, need to know *why* a document failed, or want to retrieve over what you ingested.

This project extracts document ingestion into a standalone service with a clear contract: **raw files go in; deduplicated, embedded, searchable, RAG-ready chunks come out.** It is **offline-first** — it runs and is fully tested with **no API keys and no database** — and **real-when-keyed**: set `OPENAI_API_KEY` for real embeddings, point `DATABASE_URL` at PostgreSQL for persistence. It feeds [`rag-evaluation-lab`](../rag-evaluation-lab/) and [`personal-knowledge-base-os`](../personal-knowledge-base-os/).

## What It Demonstrates

- **Multi-format parsing via `shared_core.docparse`** — `get_parser()` dispatches `.txt`/`.md`/`.html`/`.pdf`/`.docx` to a uniform `ParsedDocument` (text + title + metadata + page count). Heavy deps (PyMuPDF, python-docx, BeautifulSoup) are dynamically imported; missing ones become a clean `ParseError`.
- **Content-hash deduplication** — `compute_hash` + `filter_duplicates` skip already-ingested documents (no duplicate work) and drop repeated chunks before embedding.
- **Metadata extraction** — title (heading / `<title>` / first line), author (`By:`/`Author:` heuristics + core props), dates (multiple formats), word/char counts, page count.
- **Heuristic entity extraction** — emails, URLs, phone numbers, and capitalised n-grams (a dependency-free proper-noun proxy; no spaCy required).
- **Configurable chunking via `shared_core.docparse.chunk_text`** — fixed / semantic / structural strategies.
- **Offline-first embeddings via `shared_core.embeddings`** — deterministic `HashFallbackProvider` with no key; real OpenAI embeddings when `OPENAI_API_KEY` is set.
- **Vector similarity search via `shared_core.vectorstore`** — chunk vectors indexed into an in-memory store (offline) or pgvector (with a database); `POST /search` does cosine retrieval.
- **Error quarantine** — unparseable files are recorded (with their bytes), listed via `GET /quarantine`, and **reprocessable**.
- **DB persistence with graceful in-memory fallback** — a `db_available` probe selects PostgreSQL (documents / chunks / jobs / quarantine) when reachable, else an in-memory store, so tests and the demo run with no database. Alembic migration included.
- **Real Celery worker** — `process_document_task` and `batch_ingest_task` built on `shared_core.tasks.create_celery_app`, importable with no broker, wired to `POST /ingest/batch?async`.
- **RAG-ready JSONL export** — `GET /export/{id}` emits `{id, text, metadata}` records for downstream retrieval systems.

## Architecture

```mermaid
graph TD
    subgraph API["FastAPI (main.py)"]
        I["POST /ingest, /ingest/text, /ingest/batch"]
        B["GET /documents, /documents/id/chunks"]
        S["POST /search"]
        Q["GET /quarantine, reprocess"]
        X["GET /export/id"]
    end

    I --> P["DocumentPipeline"]
    P --> PA["DocumentParser<br/>(shared_core.docparse)"]
    PA --> CL["clean_extracted_text"]
    CL --> MD["extract_metadata + entities"]
    MD --> CH["Chunker<br/>(shared_core.docparse.chunk_text)"]
    CH --> DD["dedup_chunks<br/>(filter_duplicates)"]
    DD --> EM["EmbeddingGenerator<br/>(shared_core.embeddings)"]
    EM --> ST["Document Store"]
    EM --> VS["Vector Store<br/>(shared_core.vectorstore)"]

    P -.parse/format error.-> QU[("Quarantine")]
    S --> VS
    B --> ST
    X --> ST

    ST -->|db_available| PG[("PostgreSQL")]
    ST -->|offline fallback| MEM[("In-memory")]
    VS -->|db_available| PGV[("pgvector")]
    VS -->|offline fallback| IMV[("InMemoryVectorStore")]

    BATCH["POST /ingest/batch?async"] --> W["Celery worker<br/>(shared_core.tasks)"]
    W --> P

    style API fill:#009688,color:white
    style W fill:#37814A,color:white
    style PG fill:#4169E1,color:white
    style PGV fill:#4169E1,color:white
```

The pipeline is **store-agnostic**: `DocumentPipeline` receives a document store and a vector store, so the identical code runs against in-memory backends (tests/demo) or PostgreSQL + pgvector (production). Failures never abort a batch — they are quarantined and can be reprocessed.

## Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **API Framework** | FastAPI + Uvicorn | Async-native, automatic OpenAPI docs, Pydantic validation |
| **Parsing / chunking / dedup** | `shared_core.docparse` | Single shared ingestion layer (PyMuPDF/python-docx/bs4, chunk strategies, SHA-256 dedup) |
| **Embeddings** | `shared_core.embeddings` | Offline hash fallback by default; real OpenAI when keyed |
| **Vector search** | `shared_core.vectorstore` | In-memory cosine store offline; pgvector with a DB |
| **Background Jobs** | Celery 5.3 + `shared_core.tasks` | Async batch ingestion; importable with no broker |
| **Database** | PostgreSQL 16 (pgvector) + SQLAlchemy + Alembic | Document/chunk/job/quarantine persistence with migrations |
| **Persistence fallback** | In-memory store | `db_available` probe → runs with no database |
| **Lint / Format** | Ruff | E/W/F/I/C/B rules |
| **Testing** | pytest | Offline unit + integration + API + worker + smoke tests |

## Local Setup

```bash
cd document-intelligence-pipeline
cp .env.example .env

# Create a venv and install (shared-core extras provide the heavy parsers/embeddings)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '../shared-core[dev,docparse,embeddings]'
pip install -e '.[dev]'

# Optional: real persistence (PostgreSQL pgvector + Redis)
docker compose up -d
make upgrade            # apply the Alembic migration

make dev                # FastAPI on http://localhost:8000  (Swagger at /docs)
```

With **no** Docker and **no** keys, the API still boots: it uses the in-memory store, the in-memory vector store, and deterministic offline embeddings.

## Demo

```bash
make demo               # python examples/run_demo.py
```

The demo ingests a small in-memory corpus through the full pipeline and prints: per-document ingest status (completed / duplicate / quarantined), extracted entities, the error quarantine, a similarity-search result, and a RAG-ready JSONL line — all offline, exiting 0.

## Tests

```bash
make test               # pytest -q
```

Coverage spans every core module and the end-to-end flow, with **no network and no real DB** (uses `shared_core.testing.MockDatabase` and the offline providers):

- **Unit** — parsers (incl. PDF/DOCX behind optional-dep skips), chunkers, embeddings, metadata, entities, dedup, exporters, models, in-memory + DB stores.
- **Integration** — full pipeline ingest, dedup, quarantine + reprocess, search; persistence against SQLite.
- **API** — every endpoint, success and error paths.
- **Worker** — single + batch task logic, dedup, quarantine (no broker).
- **Smoke** — the demo runs and exits 0.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Ingest a single uploaded file (multipart). |
| `POST` | `/ingest/text` | Ingest a raw text/markdown/html string (JSON body). |
| `POST` | `/ingest/batch` | Ingest a batch synchronously, or `async_mode: true` → Celery worker. |
| `GET`  | `/documents` | List ingested documents with summary metadata. |
| `GET`  | `/documents/{id}` | Full metadata + entities for one document. |
| `GET`  | `/documents/{id}/chunks` | Ordered chunks of a document. |
| `POST` | `/search` | Embed a query and return the top-k most similar chunks. |
| `GET`  | `/quarantine` | List documents that failed processing. |
| `POST` | `/quarantine/{id}/reprocess` | Re-run ingestion for a quarantined document. |
| `GET`  | `/export/{id}` | Export a document's chunks as RAG-ready JSONL. |
| `GET`  | `/health` | Database + Redis connectivity. |
| `GET`  | `/docs` | Swagger / OpenAPI. |

### Examples

```bash
# Ingest text
curl -X POST localhost:8000/ingest/text \
  -H 'content-type: application/json' \
  -d '{"filename":"note.md","text":"# Title\n\nQuantum computing uses qubits."}'

# Search
curl -X POST localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query":"qubits superposition","top_k":3}'

# Export RAG-ready JSONL
curl localhost:8000/export/<document_id>
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `document-intelligence-pipeline` | Service id in logs/health |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/postgres` | PostgreSQL (pgvector). Unreachable → in-memory fallback |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker / result backend |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis | Worker transport |
| `OPENAI_API_KEY` | — | When set, real OpenAI embeddings; else offline hash fallback |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Known Limitations

- **Entity extraction is heuristic** — regex emails/URLs/phones + capitalised n-grams, not a trained NER model. Expect false positives on capitalised phrases.
- **Embeddings are offline by default** — the deterministic hash fallback gives stable, *lexical-ish* vectors, not semantic ones. Set `OPENAI_API_KEY` for real semantic retrieval.
- **In-memory state is per-process** — without a database, documents/quarantine live only in the running process; restart loses them. PostgreSQL persists.
- **Chunk embeddings stored as JSON** in the relational tables — semantic search uses the separate vector store (pgvector when a DB is configured), keeping the schema SQLite-testable.
- **No auth / rate limiting / file-size caps** on endpoints yet (see roadmap).
- **PDF/DOCX need the `[docparse]` extra** — without it those formats raise a clean `ParseError` and are quarantined.

## Roadmap

- **Phase 1 — Core pipeline** *(done)*: multi-format parse, clean, chunk, embed, JSONL export.
- **Phase 2 — Intelligence & persistence** *(done)*: metadata + entity extraction, content-hash dedup, DB schema (documents/chunks/jobs/quarantine) + Alembic, error quarantine + reprocess, vector search, real Celery batch worker, offline-first embeddings.
- **Phase 3 — Showcase**: webhook callbacks on completion, chunk-preview highlighting, processing-throughput metrics endpoint, deeper integration hooks for `rag-evaluation-lab`.
- **Phase 4 — Future**: table/image extraction from PDFs, OCR fallback (Tesseract), trained NER, topic-boundary semantic chunking, incremental re-processing of changed files.

See [`docs/`](docs/) for architecture, design decisions, failure modes, security, and the execution plan.

## License

MIT — see [LICENSE](LICENSE).
