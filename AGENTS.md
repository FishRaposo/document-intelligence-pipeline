# AGENTS.md — document-intelligence-pipeline

## What This Is

A multi-stage document processing pipeline that ingests raw files (txt, md, html — with planned pdf/docx support), cleans extracted text, splits it into overlapping semantic chunks using a sliding-window algorithm, generates vector embeddings, and exports structured JSONL for downstream RAG systems. Part of Wave 1 in the showcase portfolio. Feeds into `rag-evaluation-lab` and `personal-knowledge-base-os`.

## Commands

```bash
make install          # pip install -e ../shared-core && pip install -r requirements.txt
make dev              # python src/doc_pipeline/main.py (FastAPI on :8000)
make test             # pytest (runs tests/test_core.py)
make lint             # ruff check .
make format           # ruff format .
make typecheck        # pyright src/
make docker-up        # docker compose up -d (Postgres pgvector:pg16 + Redis 7)
make docker-down      # docker compose down
make demo             # python examples/run_demo.py (end-to-end pipeline demo)
make clean            # remove __pycache__, .pytest_cache, etc.
```

## Entry Point

`src/doc_pipeline/main.py` — FastAPI app with two endpoints:
- `POST /ingest` — accepts `UploadFile`, decodes UTF-8, runs `clean_extracted_text()` → `SlidingWindowChunker.chunk_text()`, returns chunks as JSON
- `GET /health` — checks PostgreSQL (`DatabaseManager`) and Redis (`RedisManager`) connectivity

Imports: `AppConfig` from `.config`, `DocumentParser` from `.parsers`, `clean_extracted_text` from `.cleaners`, `SlidingWindowChunker` from `.chunkers`, `application_error_handler` from `.errors`.

## Source Modules

```
src/doc_pipeline/
├── __init__.py       # Package marker
├── main.py           # FastAPI app, /ingest and /health endpoints
├── config.py         # AppConfig(BaseAppConfig) — APP_NAME override
├── parsers.py        # DocumentParser — dispatches .txt/.md/.html parsing
├── cleaners.py       # clean_extracted_text() — regex whitespace normalization
├── chunkers.py       # SlidingWindowChunker — overlapping word-based chunks
├── embeddings.py     # MockEmbeddingGenerator — deterministic hash-based vectors
├── exporters.py      # JSONLExporter — writes chunk dicts as JSONL
├── worker.py         # Celery app + sample_background_task (placeholder)
└── errors.py         # application_error_handler for BaseApplicationError
```

## Docker Services

- **postgres**: `pgvector/pgvector:pg16` on `:5432` — container name `template_postgres`
- **redis**: `redis:7-alpine` on `:6379` — container name `template_redis`

## Layout

```
document-intelligence-pipeline/
├── src/doc_pipeline/        # All source code (see modules above)
├── tests/test_core.py       # Health endpoint test
├── examples/run_demo.py     # End-to-end pipeline demo (parse → clean → chunk → embed)
├── docs/                    # architecture.md, design-decisions.md, failure-modes.md, roadmap.md, security.md
├── .github/workflows/ci.yml # ruff check, ruff format --check, pytest
├── docker-compose.yml       # Postgres + Redis
├── Makefile                 # Standard targets
├── .env.example             # APP_NAME, DATABASE_URL, REDIS_URL, API keys
├── pyproject.toml           # Project metadata (description still template placeholder)
├── requirements.txt         # fastapi, uvicorn, pydantic, httpx, celery, redis, sqlalchemy, loguru, pyyaml
├── ruff.toml                # Python 3.10, line-length 88, E/W/F/I/C/B rules
├── pyrightconfig.json       # basic type checking mode
└── pytest.ini               # testpaths = tests, verbose
```

## Current State

**Skeleton with functional pipeline stages.** The core parse → clean → chunk path works end-to-end for plain text files (verified via `examples/run_demo.py`). However:

- `DocumentParser` only handles `.txt`, `.md`, `.html` — PDF/DOCX raise `ValueError`
- HTML parsing uses naive string replacement, not DOM parsing
- Markdown parsing only strips `#` characters
- `POST /ingest` decodes raw bytes as UTF-8 — bypasses `DocumentParser` entirely, no format detection
- `MockEmbeddingGenerator` produces deterministic vectors, not real embeddings
- `JSONLExporter` exists but is not wired into the `/ingest` endpoint
- `worker.py` has a placeholder task (`sample_background_task`) — no document processing task
- No database schema exists — PostgreSQL container runs but no tables are created
- `pyproject.toml` description is still the template placeholder

## Key Dependencies

Beyond shared-core (`config`, `database`, `redis`, `logging`, `errors`):

| Package | Purpose |
|---------|---------|
| `celery` | Background document processing tasks |
| `redis` | Celery broker and result backend |
| `sqlalchemy` | Database ORM (used in health check) |
| `loguru` | Structured logging |
| `pyyaml` | Configuration parsing |
| `httpx` | HTTP client (for future webhook callbacks) |

**Not yet added but needed:** `pdfplumber` or `pymupdf` (PDF parsing), `python-docx` (DOCX), `beautifulsoup4` (HTML), `openai` or `sentence-transformers` (real embeddings), `pgvector` (SQLAlchemy vector extension).

## When to Update This AGENTS.md

- When new parsers are added (PDF, DOCX) or parser dispatch logic changes
- When `POST /ingest` is updated to use `DocumentParser` or support binary uploads
- When Celery tasks are created for async document processing
- When database schema/models are added for documents and chunks
- When `MockEmbeddingGenerator` is replaced with real embedding integration
- When new API endpoints are added (batch upload, status, export)
- When Docker Compose services change (e.g., adding a Celery worker service)
- When project moves from skeleton to functional state
