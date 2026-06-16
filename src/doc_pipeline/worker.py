"""Celery worker with real document-processing tasks.

Built on ``shared_core.tasks.create_celery_app``. The module is importable with
NO broker running (Celery only connects when a worker starts or ``.delay()`` is
called), so tests and the API import it freely. Two domain tasks are exposed:

- ``process_document_task`` — ingest a single base64-encoded document.
- ``batch_ingest_task``     — ingest a batch of documents, quarantining failures.

Both build a fresh store + vector store via the ``db_available`` probe so a worker
process persists to PostgreSQL when a database is reachable, and to an in-memory
store otherwise. The pure logic lives in ``_process_one`` / ``_process_batch`` so
it can be unit-tested without invoking Celery.
"""

import base64
from typing import Any, Dict, List

from shared_core.tasks import create_celery_app
from shared_core.vectorstore import get_vector_store

from . import db as db_module
from .config import AppConfig
from .pipeline import DocumentPipeline

config = AppConfig()
celery_app = create_celery_app(
    config.APP_NAME,
    broker_url=config.CELERY_BROKER_URL,
    backend_url=config.CELERY_RESULT_BACKEND,
)


def _build_pipeline() -> DocumentPipeline:
    """Construct a pipeline bound to the active (DB or in-memory) store."""
    db_module.check_db()
    store = db_module.build_store()
    vector_store = get_vector_store(
        offline=not db_module.db_available,
        db_manager=db_module.db_manager if db_module.db_available else None,
    )
    return DocumentPipeline(store, vector_store)


def _process_one(filename: str, content_b64: str) -> Dict[str, Any]:
    """Pure single-document processing (no Celery dependency)."""
    pipeline = _build_pipeline()
    content = base64.b64decode(content_b64) if content_b64 else b""
    result = pipeline.ingest(content, filename)
    return result.to_dict()


def _process_batch(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """Pure batch processing: ``documents`` is a list of {filename, content_b64}."""
    pipeline = _build_pipeline()
    results: List[Dict[str, Any]] = []
    completed = duplicates = quarantined = 0
    for doc in documents:
        content = base64.b64decode(doc.get("content_b64", "") or "")
        outcome = pipeline.ingest(content, doc.get("filename", "untitled"))
        results.append(outcome.to_dict())
        if outcome.status == "completed":
            completed += 1
        elif outcome.status == "duplicate":
            duplicates += 1
        else:
            quarantined += 1
    return {
        "status": "completed",
        "total": len(documents),
        "completed": completed,
        "duplicates": duplicates,
        "quarantined": quarantined,
        "results": results,
    }


@celery_app.task(name="doc_pipeline.process_document")
def process_document_task(filename: str, content_b64: str) -> Dict[str, Any]:
    """Celery task: ingest a single base64-encoded document."""
    return _process_one(filename, content_b64)


@celery_app.task(name="doc_pipeline.batch_ingest")
def batch_ingest_task(documents: List[Dict[str, str]]) -> Dict[str, Any]:
    """Celery task: ingest a batch of documents, quarantining failures."""
    return _process_batch(documents)
