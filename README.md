# Document Intelligence Pipeline

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3+-37814A?logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

**A multi-stage document processing pipeline that converts raw files (PDF, DOCX, HTML, Markdown, plain text) into structured, semantically chunked, vector-embedded knowledge — ready for RAG retrieval and downstream AI consumption.**

## Why This Exists

Every RAG system, knowledge base, and AI agent depends on the same unglamorous upstream work: turning messy, heterogeneous documents into clean, chunked, embedded data. Most teams cobble this together as a one-off script buried inside their retrieval codebase. That approach breaks the moment you need to handle a second file format, track processing failures, or change your chunking strategy without re-ingesting everything.

This project extracts document ingestion into its own standalone pipeline with a clear contract: raw files go in, JSONL chunks with embeddings come out. It handles format-specific parsing, text normalization, configurable sliding-window chunking, embedding generation, and structured export — each as an isolated, testable stage. The pipeline is designed to feed directly into [`rag-evaluation-lab`](../rag-evaluation-lab/) for retrieval quality testing and [`personal-knowledge-base-os`](../personal-knowledge-base-os/) for persistent knowledge storage.

## What It Demonstrates

- **Multi-format document parsing** — extensible `DocumentParser` class dispatching to format-specific extractors (`.txt`, `.md`, `.html`, with planned `.pdf` and `.docx` support)
- **Text cleaning and normalization** — `clean_extracted_text()` pipeline stage for whitespace normalization and junk character removal
- **Sliding-window chunking with overlap** — `SlidingWindowChunker` producing overlapping chunks to preserve cross-boundary context for retrieval
- **Vector embedding generation** — `MockEmbeddingGenerator` producing deterministic 1536-dimensional vectors (swappable with OpenAI/sentence-transformers)
- **Structured JSONL export** — `JSONLExporter` writing chunk-level records for downstream consumption
- **Background job architecture** — Celery worker with Redis broker for async document processing at scale
- **FastAPI REST ingestion** — `POST /ingest` endpoint accepting file uploads and returning chunked results synchronously
- **Health monitoring** — `/health` endpoint with database and Redis connectivity checks

## Architecture

```mermaid
graph TD
    A["Client / File Upload"] --> B["FastAPI Gateway"]
    B --> C["DocumentParser"]
    C --> D["clean_extracted_text()"]
    D --> E["SlidingWindowChunker"]
    E --> F["MockEmbeddingGenerator"]
    F --> G["JSONLExporter"]

    B --> H["Celery Worker"]
    H --> C

    B -.-> I[("PostgreSQL (pgvector)")]
    H -.-> J["Redis Queue"]

    style B fill:#009688,color:white
    style H fill:#37814A,color:white
    style I fill:#4169E1,color:white
    style J fill:#DC382D,color:white
```

Documents flow through a linear pipeline: **Parse → Clean → Chunk → Embed → Export**. The FastAPI layer handles synchronous ingestion via `POST /ingest`, while Celery workers (planned) will process batch and folder ingestion asynchronously through Redis.

## Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **API Framework** | FastAPI + Uvicorn | Async-native, automatic OpenAPI docs, Pydantic validation |
| **Background Jobs** | Celery 5.3 + Redis | Proven task queue for long-running document processing |
| **Database** | PostgreSQL 16 (pgvector) | Vector storage for embeddings, relational metadata tracking |
| **Cache / Broker** | Redis 7 | Celery broker + result backend + processing status cache |
| **Text Processing** | Python stdlib `re` | Minimal dependencies for text normalization |
| **Embedding** | Mock (swappable) | Deterministic vectors for development; production uses OpenAI or sentence-transformers |
| **Export** | JSONL | Streaming-friendly, line-by-line processable, standard for ML pipelines |
| **Shared Library** | [`shared-core`](../shared-core/) | Config, database, Redis, logging, and error handling |
| **Lint / Format** | Ruff | Fast linting (E, W, F, I, C, B rules) and formatting |
| **Type Checking** | Pyright | Static type analysis in basic mode |
| **Testing** | pytest | Standard test runner with verbose output |

## Local Setup

```bash
# Clone and enter directory
cd document-intelligence-pipeline

# Copy example environment
cp .env.example .env

# Start local infrastructure (Postgres pgvector + Redis)
docker compose up -d

# Install dependencies (installs shared-core first, then requirements.txt)
make install

# Run the API server
make dev
```

The API starts on `http://localhost:8000`. Swagger docs are available at `/docs`.

## Demo

Run the end-to-end pipeline demo without starting the server:

```bash
make demo
```

The demo script (`examples/run_demo.py`) performs the full pipeline locally:

1. Creates a sample text document about AI and software engineering
2. Parses it with `DocumentParser`
3. Cleans the extracted text with `clean_extracted_text()`
4. Chunks it using `SlidingWindowChunker(chunk_size=15, overlap=5)`
5. Generates 128-dimensional mock embeddings for each chunk via `MockEmbeddingGenerator`
6. Prints each chunk with its content and vector size

**Expected output:**

```
--- Processing sample_doc.txt through Ingestion Pipeline ---
Extracted 4 overlapping semantic chunks:
 Chunk 0: 'Artificial intelligence is transforming...' (Vector size: 128)
 Chunk 1: 'Modern IDEs feature intelligent...' (Vector size: 128)
 ...
```

## Tests

```bash
make test
```

Current test coverage (`tests/test_core.py`):
- **Health endpoint validation** — verifies `GET /health` returns 200 with correct service name and dependency status structure
- Tests run via pytest with verbose output and require the FastAPI app to initialize (database/Redis connections will report as `offline` if Docker services aren't running)

Planned test additions: parser unit tests per format, chunker boundary tests, exporter output validation, end-to-end pipeline tests.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest` | Upload a file for processing. Returns filename, total chunk count, and chunk array |
| `GET` | `/health` | Infrastructure health check. Reports database and Redis connectivity status |
| `GET` | `/docs` | Auto-generated Swagger/OpenAPI documentation |

### `POST /ingest` Example

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@document.txt"
```

**Response:**
```json
{
  "filename": "document.txt",
  "total_chunks": 3,
  "chunks": [
    {"chunk_id": 0, "content": "...", "word_count": 200},
    {"chunk_id": 1, "content": "...", "word_count": 200},
    {"chunk_id": 2, "content": "...", "word_count": 150}
  ]
}
```

## Configuration

Key environment variables from `.env.example`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `document-intelligence-pipeline` | Service identifier in logs and health checks |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/postgres` | PostgreSQL connection (pgvector-enabled) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for Celery broker and result backend |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG` | `true` | Development mode toggle |
| `OPENAI_API_KEY` | — | Required when swapping `MockEmbeddingGenerator` for OpenAI embeddings |

## Known Limitations

- **PDF and DOCX parsing not yet implemented** — `DocumentParser` currently supports `.txt`, `.md`, and `.html` only; PDF/DOCX raise `ValueError`
- **HTML parser is naive** — strips `<html>` tags with string replacement rather than proper DOM parsing (no BeautifulSoup/lxml)
- **Markdown parser strips all `#` characters** — removes heading markers but doesn't handle other Markdown syntax (bold, links, lists)
- **`POST /ingest` assumes UTF-8 text** — binary files (actual PDFs) will fail with decode errors; no content-type detection
- **Embedding generator is deterministic mock** — produces hash-based vectors, not real semantic embeddings
- **Celery worker has only a placeholder task** — `sample_background_task` adds two integers; no actual document processing task exists yet
- **No database schema** — PostgreSQL is in Docker Compose but no tables are created; document/chunk metadata isn't persisted
- **No deduplication** — identical documents or chunks are processed repeatedly without detection
- **No file size limits** — the `/ingest` endpoint accepts arbitrarily large uploads

## Roadmap

- **Phase 1 — MVP Core Pipeline** *(current)*
  - [x] Multi-format parser skeleton (txt, md, html)
  - [x] Text cleaning stage
  - [x] Sliding-window chunker with configurable size/overlap
  - [x] Mock embedding generator
  - [x] JSONL exporter
  - [x] FastAPI `/ingest` endpoint
  - [x] Celery worker scaffold
  - [ ] PDF parser (`pdfplumber` or `pymupdf`)
  - [ ] DOCX parser (`python-docx`)
  - [ ] Proper HTML parser (`beautifulsoup4`)

- **Phase 2 — Display-Ready Pipeline**
  - [ ] Database schema for documents, chunks, and processing status
  - [ ] Celery task for async document ingestion
  - [ ] Metadata extraction (title, author, dates, page count)
  - [ ] Content-hash deduplication at document and chunk level
  - [ ] Processing status tracking (queued → processing → completed → failed)
  - [ ] Error quarantine for unparseable documents
  - [ ] Real embedding integration (OpenAI `text-embedding-3-small` or sentence-transformers)

- **Phase 3 — Showcase Features**
  - [ ] Folder/batch ingestion endpoint
  - [ ] Chunk preview API with highlighting
  - [ ] Entity extraction (spaCy NER)
  - [ ] Processing dashboard with status metrics
  - [ ] RAG-ready export with integration hooks for [`rag-evaluation-lab`](../rag-evaluation-lab/)
  - [ ] Webhook callbacks on processing completion

- **Phase 4 — Future Improvements**
  - [ ] Table and image extraction from PDFs
  - [ ] OCR fallback for scanned documents (Tesseract)
  - [ ] Semantic chunking (split on topic boundaries, not just word count)
  - [ ] Incremental re-processing (detect changed files, re-chunk only diffs)
  - [ ] Prometheus metrics for pipeline throughput and error rates
