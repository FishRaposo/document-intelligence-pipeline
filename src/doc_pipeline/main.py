"""FastAPI application for the Document Intelligence Pipeline.

Offline-first: boots and serves with NO database (in-memory document + vector
stores) and NO API keys (deterministic offline embeddings). When a database is
reachable, documents/chunks/jobs/quarantine persist to PostgreSQL via the
``db_available`` probe, and vectors persist to pgvector. Exposes everything a
dashboard needs: ingestion (sync + batch), document/chunk browsing, similarity
search, the error quarantine (list + reprocess), and JSONL export.
"""

import base64
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from shared_core.errors import (
    BaseApplicationError,
    NotFoundError,
    ValidationError,
    application_error_handler,
)
from shared_core.health import check_health
from shared_core.logging import RequestLoggingMiddleware, setup_logging
from shared_core.redis import RedisManager
from shared_core.vectorstore import get_vector_store

from . import db as db_module
from .config import AppConfig
from .exporters import JSONLExporter, to_rag_records
from .pipeline import DocumentPipeline
from .storage import InMemoryDocumentStore

config = AppConfig()
setup_logging(level=config.LOG_LEVEL, service_name=config.APP_NAME)

# Offline-first defaults; the startup probe upgrades ``store`` to a DB-backed
# store when a database is reachable. Tests patch these module globals directly.
store: object = InMemoryDocumentStore()
vector_store = get_vector_store(offline=True)
pipeline = DocumentPipeline(store, vector_store)

db_manager = db_module.db_manager
redis_manager = RedisManager(config.REDIS_URL)


def _rebuild_pipeline() -> None:
    """Rebuild the module-level pipeline against the current store/vector store."""
    global pipeline
    pipeline = DocumentPipeline(store, vector_store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Probe the database on startup and select persistence backends."""
    global store, vector_store
    db_module.check_db()
    if db_module.db_available:
        store = db_module.build_store()
        vector_store = get_vector_store(offline=False, db_manager=db_module.db_manager)
        if hasattr(vector_store, "setup"):
            try:
                vector_store.setup()
            except Exception:  # noqa: BLE001 - non-fatal; fall back to in-memory
                vector_store = get_vector_store(offline=True)
        _rebuild_pipeline()
    yield


app = FastAPI(
    title=config.APP_NAME,
    version="1.0.0",
    description=(
        "Multi-stage document ingestion: parse, clean, chunk, dedup, embed, and "
        "export documents into RAG-ready chunks with similarity search and an "
        "error quarantine."
    ),
    lifespan=lifespan,
)

app.add_exception_handler(BaseApplicationError, application_error_handler)
app.add_middleware(RequestLoggingMiddleware)


# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #
class TextIngestRequest(BaseModel):
    """Ingest a raw text/markdown/html string instead of a file upload."""

    filename: str = Field(default="document.txt")
    text: str


class BatchDocument(BaseModel):
    """One document in a batch ingestion request (raw text)."""

    filename: str
    text: str


class BatchIngestRequest(BaseModel):
    documents: List[BatchDocument]
    async_mode: bool = Field(
        default=False, description="Dispatch to the Celery worker when true."
    )


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


# --------------------------------------------------------------------------- #
# Ingestion
# --------------------------------------------------------------------------- #
@app.post("/ingest")
async def ingest_document(
    file: Optional[UploadFile] = None,
):
    """Ingest a single uploaded file. Falls back to a JSON body via ``/ingest/text``."""
    if file is None:
        raise ValidationError("Provide a file upload, or POST text to /ingest/text.")
    content = await file.read()
    filename = file.filename or "untitled"
    result = pipeline.ingest(content, filename)
    return result.to_dict()


@app.post("/ingest/text")
def ingest_text(payload: TextIngestRequest):
    """Ingest a raw text/markdown/html string."""
    content = payload.text.encode("utf-8")
    result = pipeline.ingest(content, payload.filename)
    return result.to_dict()


@app.post("/ingest/batch")
def ingest_batch(payload: BatchIngestRequest):
    """Ingest a batch of documents synchronously, or dispatch to the worker."""
    if payload.async_mode:
        from .worker import batch_ingest_task

        docs = [
            {
                "filename": d.filename,
                "content_b64": base64.b64encode(d.text.encode("utf-8")).decode("ascii"),
            }
            for d in payload.documents
        ]
        task = batch_ingest_task.delay(docs)
        return {"task_id": task.id, "status": "queued", "count": len(docs)}

    results = [
        pipeline.ingest(d.text.encode("utf-8"), d.filename) for d in payload.documents
    ]
    return {
        "total": len(results),
        "completed": sum(1 for r in results if r.status == "completed"),
        "duplicates": sum(1 for r in results if r.status == "duplicate"),
        "quarantined": sum(1 for r in results if r.status == "quarantined"),
        "results": [r.to_dict() for r in results],
    }


# --------------------------------------------------------------------------- #
# Browsing
# --------------------------------------------------------------------------- #
@app.get("/documents")
def list_documents():
    """List all ingested documents with summary metadata."""
    return {"documents": store.list_documents()}


@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    """Return a single document's full metadata and entities."""
    doc = store.get_document(doc_id)
    if doc is None:
        raise NotFoundError(f"Document '{doc_id}' not found")
    return doc


@app.get("/documents/{doc_id}/chunks")
def get_document_chunks(doc_id: str):
    """Return the ordered chunks of a document."""
    if store.get_document(doc_id) is None:
        raise NotFoundError(f"Document '{doc_id}' not found")
    return {"document_id": doc_id, "chunks": store.get_chunks(doc_id)}


# --------------------------------------------------------------------------- #
# Search
# --------------------------------------------------------------------------- #
@app.post("/search")
def search(payload: SearchRequest):
    """Embed the query and return the most similar stored chunks."""
    return {
        "query": payload.query,
        "results": pipeline.search(payload.query, payload.top_k),
    }


# --------------------------------------------------------------------------- #
# Quarantine
# --------------------------------------------------------------------------- #
@app.get("/quarantine")
def list_quarantine():
    """List documents that failed processing and are awaiting reprocessing."""
    return {"quarantine": store.list_quarantine()}


@app.post("/quarantine/{entry_id}/reprocess")
def reprocess_quarantine(entry_id: str):
    """Re-run ingestion for a quarantined document."""
    result = pipeline.reprocess_quarantine(entry_id)
    if result is None:
        raise NotFoundError(f"Quarantine entry '{entry_id}' not found")
    return result.to_dict()


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
@app.get("/export/{doc_id}")
def export_document(doc_id: str):
    """Export a document's chunks as RAG-ready JSONL."""
    doc = store.get_document(doc_id)
    if doc is None:
        raise NotFoundError(f"Document '{doc_id}' not found")
    chunks = store.get_chunks(doc_id)
    records = to_rag_records(doc, chunks)
    body = JSONLExporter().dumps(records)
    return PlainTextResponse(body, media_type="application/x-ndjson")


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health")
def health_check():
    """Service health, probing database and Redis connectivity."""
    return check_health(db_manager, redis_manager, config.APP_NAME)


def main():
    """Run the development server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
