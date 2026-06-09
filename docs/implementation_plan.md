# Implementation Plan - Document Intelligence Pipeline

This document details the step-by-step technical implementation plan and development milestones for **Document Intelligence Pipeline**.

---

## 1. Project Goal
An ingestion and processing engine that parses PDF, HTML, and Word documents, partitions them using semantic and fixed chunking, generates metadata, and publishes semantic vectors.

---

## 2. Architecture & Component Map

The repository is structured as a standalone project conforming to operator workspace standards. The core module responsibilities are mapped below:

### 2.1 File Map & Responsibilities
* **`src/doc_pipeline/extractor.py`**: Extracts raw text and structures from PDFs, DOCX, and HTML payloads.
* **`src/doc_pipeline/chunker.py`**: Segments raw text using fixed limits or semantic similarity bounds (sentence splitting).
* **`src/doc_pipeline/metadata.py`**: Uses lightweight token checks to generate metadata tags (author, section, core topics).
* **`src/doc_pipeline/publisher.py`**: Converts chunks into embeddings and stores them in pgvector vector tables.

### 2.2 Shared Core Dependencies
This service imports standard layers from `shared-core` (sibling dependency library):
* `shared_core.config.BaseAppConfig`: Settings parsing, reading configs from `.env`.
* `shared_core.database.DatabaseManager`: SQL database engine instantiation and session factories.
* `shared_core.redis.RedisManager`: Caching connections and health checks.
* `shared_core.logging.setup_logging`: Structured log formats and correlation ID tracing.
* `shared_core.errors.BaseApplicationError`: Exception mapping and global handlers.

---

## 3. Database Schema & Data Models

### 3.1 Data Schema
PostgreSQL (pgvector): `documents` (id, filename, file_hash, size_bytes, uploaded_at), `document_chunks` (id, document_id, chunk_index, content, metadata_json, embedding_vector: vector(1536)).
Redis: Rate-limits and indexing progress queues.

### 3.2 Redis Storage & Caching Patterns
* Caching: Utilizing `@cache` decorator with prefix keys.
* Concurrency: Lock critical tasks using `RedisLock` context managers.

---

## 4. Step-by-Step Implementation Sequence

The project development checklist is ordered into six milestones:

- `[ ]` **Milestone 1 (Design): Plan document chunking strategies and pgvector embedding sizes.**
- `[ ]` **Milestone 2 (Skeleton): Setup FastAPI document uploads router and configure shared DB connection pools.**
- `[ ]` **Milestone 3 (Core Loop): Build file parsing parsers and semantic chunk splitter.**
- `[ ]` **Milestone 4 (Reliability): Handle corrupt file formats and API rate-limiting errors.**
- `[ ]` **Milestone 5 (Showcase): Runnable pipeline demo ingest PDF manuals, generate metadata, and search chunks semantically.**
- `[ ]` **Milestone 6 (Publish): Document parsing failure boundaries, token sizes, and vector database index structures.**

---

## 5. Standard Makefile & Developer Commands

```bash
make install          # Set up virtual environment and local editable package
make dev              # Boot the microservice API server locally
make test             # Run local pytest / jest test suites
make lint             # Execute Ruff checks / ESLint verifications
make format           # Standardize style formatting
make typecheck        # Verify static types (Pyright / TypeScript)
make docker-up        # Spawn isolated local PostgreSQL and Redis service containers
make docker-down      # Teardown the isolated local containers stack
make demo             # Execute the runnable demo workflow
make clean            # Remove caches and temporary files
```

---

## 6. Verification & Testing Plan

### 6.1 Automated Tests
* **Core Logic Verification**: Assert text extraction accuracy, chunk sizing limits, vector insertion, and metadata extraction boundaries.
* **Type Safety & Style**: Run `make typecheck` and `make lint` as a pipeline validation hook.
* **Mock Environments**: Utilize `MockDatabase` and `MockRedisClient` inside `tests/conftest.py` to assert correct lifecycle transactions without depending on live network services.

### 6.2 Manual Verification
* Deploy local PostgreSQL and Redis containers with `make docker-up`.
* Execute the runnable script demo `make demo` and review Loguru stdout records.
