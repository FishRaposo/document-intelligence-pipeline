"""In-memory document/chunk/job/quarantine store — the offline default.

Implements the same interface as :class:`storage_db.DatabaseDocumentStore` so the
API, pipeline, and worker run identically with NO database (tests and the demo).
Document-level content-hash dedup is enforced here too: saving a document whose
hash already exists returns the existing id instead of creating a duplicate.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryDocumentStore:
    """Process-local store for documents, chunks, jobs, and quarantine."""

    def __init__(self) -> None:
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._hash_index: Dict[str, str] = {}
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._quarantine: Dict[str, Dict[str, Any]] = {}

    # -- documents & chunks -------------------------------------------------
    def find_by_hash(self, content_hash: str) -> Optional[str]:
        """Return an existing document id for ``content_hash`` if present."""
        return self._hash_index.get(content_hash)

    def save_document(
        self,
        *,
        filename: str,
        file_format: str,
        file_size: int,
        content_hash: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist a document and its chunks; dedups on ``content_hash``."""
        existing = self._hash_index.get(content_hash)
        if existing is not None:
            return existing

        doc_id = str(uuid.uuid4())
        metadata = metadata or {}
        self._documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "format": file_format,
            "file_size_bytes": file_size,
            "total_chunks": len(chunks),
            "content_hash": content_hash,
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "word_count": metadata.get("word_count", 0),
            "doc_metadata": metadata,
            "entities": entities or {},
            "created_at": _now(),
        }
        self._chunks[doc_id] = [
            {
                "id": str(uuid.uuid4()),
                "document_id": doc_id,
                "chunk_index": i,
                "content": ch.get("content", ""),
                "word_count": ch.get("word_count", 0),
                "content_hash": ch.get("content_hash"),
                "embedding": ch.get("embedding"),
            }
            for i, ch in enumerate(chunks)
        ]
        self._hash_index[content_hash] = doc_id
        return doc_id

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self._documents.get(doc_id)
        if doc is None:
            return None
        return {k: v for k, v in doc.items() if k != "doc_metadata"} | {
            "metadata": doc.get("doc_metadata", {}),
        }

    def list_documents(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": d["id"],
                "filename": d["filename"],
                "format": d["format"],
                "title": d.get("title"),
                "author": d.get("author"),
                "total_chunks": d["total_chunks"],
                "word_count": d.get("word_count", 0),
                "created_at": d["created_at"],
            }
            for d in self._documents.values()
        ]

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": c["id"],
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "word_count": c["word_count"],
            }
            for c in self._chunks.get(doc_id, [])
        ]

    def all_chunks(self) -> List[Dict[str, Any]]:
        """Return every stored chunk with its embedding (for vector indexing)."""
        out: List[Dict[str, Any]] = []
        for chunks in self._chunks.values():
            out.extend(chunks)
        return out

    # -- processing jobs ----------------------------------------------------
    def create_job(self, filename: str, status: str = "queued") -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "filename": filename,
            "status": status,
            "document_id": None,
            "total_chunks": 0,
            "error": None,
            "created_at": _now(),
        }
        return job_id

    def update_job(self, job_id: str, **fields: Any) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].update(fields)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return list(self._jobs.values())

    # -- quarantine ---------------------------------------------------------
    def quarantine(
        self,
        *,
        filename: str,
        reason: str,
        file_format: Optional[str] = None,
        file_size: int = 0,
        content_b64: Optional[str] = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        self._quarantine[entry_id] = {
            "id": entry_id,
            "filename": filename,
            "format": file_format,
            "file_size_bytes": file_size,
            "reason": reason,
            "content_b64": content_b64,
            "created_at": _now(),
        }
        return entry_id

    def list_quarantine(self) -> List[Dict[str, Any]]:
        return [
            {k: v for k, v in entry.items() if k != "content_b64"}
            for entry in self._quarantine.values()
        ]

    def get_quarantine(self, entry_id: str) -> Optional[Dict[str, Any]]:
        return self._quarantine.get(entry_id)

    def remove_quarantine(self, entry_id: str) -> bool:
        return self._quarantine.pop(entry_id, None) is not None
