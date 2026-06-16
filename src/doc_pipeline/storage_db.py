"""PostgreSQL-backed document/chunk/job/quarantine persistence.

Mirrors :class:`storage.InMemoryDocumentStore` so the API, pipeline, and worker
work against either backend unchanged. Document-level content-hash dedup is
enforced via the unique ``documents.content_hash`` column plus a lookup before
insert. Uses a session factory (the ``DatabaseManager.get_session`` generator)
exactly like the migrated services.
"""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from .models import Chunk, Document, ProcessingJob, QuarantineEntry


class DatabaseDocumentStore:
    """SQLAlchemy-backed store using a session factory."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def _session(self) -> Session:
        return next(self.session_factory())

    # -- documents & chunks -------------------------------------------------
    def find_by_hash(self, content_hash: str) -> Optional[str]:
        session = self._session()
        try:
            doc = (
                session.query(Document)
                .filter(Document.content_hash == content_hash)
                .first()
            )
            return doc.id if doc else None
        finally:
            session.close()

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
        existing = self.find_by_hash(content_hash)
        if existing is not None:
            return existing

        metadata = metadata or {}
        doc_id = str(uuid.uuid4())
        session = self._session()
        try:
            doc = Document(
                id=doc_id,
                filename=filename,
                format=file_format,
                file_size_bytes=file_size,
                total_chunks=len(chunks),
                content_hash=content_hash,
                title=metadata.get("title"),
                author=metadata.get("author"),
                word_count=metadata.get("word_count", 0),
                doc_metadata=metadata,
                entities=entities or {},
            )
            session.add(doc)
            for i, ch in enumerate(chunks):
                session.add(
                    Chunk(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        chunk_index=i,
                        content=ch.get("content", ""),
                        word_count=ch.get("word_count", 0),
                        content_hash=ch.get("content_hash"),
                        embedding=ch.get("embedding"),
                    )
                )
            session.commit()
            logger.info(f"Saved document {doc_id} with {len(chunks)} chunks")
            return doc_id
        except Exception as exc:
            session.rollback()
            logger.error(f"Failed to save document: {exc}")
            raise
        finally:
            session.close()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        session = self._session()
        try:
            doc = session.get(Document, doc_id)
            if not doc:
                return None
            return {
                "id": doc.id,
                "filename": doc.filename,
                "format": doc.format,
                "file_size_bytes": doc.file_size_bytes,
                "title": doc.title,
                "author": doc.author,
                "total_chunks": doc.total_chunks,
                "word_count": doc.word_count,
                "content_hash": doc.content_hash,
                "metadata": doc.doc_metadata or {},
                "entities": doc.entities or {},
                "created_at": doc.created_at.isoformat(),
            }
        finally:
            session.close()

    def list_documents(self) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            docs = session.query(Document).order_by(Document.created_at).all()
            return [
                {
                    "id": d.id,
                    "filename": d.filename,
                    "format": d.format,
                    "title": d.title,
                    "author": d.author,
                    "total_chunks": d.total_chunks,
                    "word_count": d.word_count,
                    "created_at": d.created_at.isoformat(),
                }
                for d in docs
            ]
        finally:
            session.close()

    def get_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            chunks = (
                session.query(Chunk)
                .filter(Chunk.document_id == doc_id)
                .order_by(Chunk.chunk_index)
                .all()
            )
            return [
                {
                    "id": c.id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "word_count": c.word_count,
                }
                for c in chunks
            ]
        finally:
            session.close()

    def all_chunks(self) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            chunks = session.query(Chunk).all()
            return [
                {
                    "id": c.id,
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "content": c.content,
                    "word_count": c.word_count,
                    "embedding": c.embedding,
                }
                for c in chunks
            ]
        finally:
            session.close()

    # -- processing jobs ----------------------------------------------------
    def create_job(self, filename: str, status: str = "queued") -> str:
        job_id = str(uuid.uuid4())
        session = self._session()
        try:
            session.add(ProcessingJob(id=job_id, filename=filename, status=status))
            session.commit()
            return job_id
        finally:
            session.close()

    def update_job(self, job_id: str, **fields: Any) -> None:
        session = self._session()
        try:
            job = session.get(ProcessingJob, job_id)
            if job is None:
                return
            for key, value in fields.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            session.commit()
        finally:
            session.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        session = self._session()
        try:
            job = session.get(ProcessingJob, job_id)
            if job is None:
                return None
            return _job_dict(job)
        finally:
            session.close()

    def list_jobs(self) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            return [
                _job_dict(j)
                for j in session.query(ProcessingJob)
                .order_by(ProcessingJob.created_at)
                .all()
            ]
        finally:
            session.close()

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
        session = self._session()
        try:
            session.add(
                QuarantineEntry(
                    id=entry_id,
                    filename=filename,
                    format=file_format,
                    file_size_bytes=file_size,
                    reason=reason,
                    content_b64=content_b64,
                )
            )
            session.commit()
            return entry_id
        finally:
            session.close()

    def list_quarantine(self) -> List[Dict[str, Any]]:
        session = self._session()
        try:
            return [
                {
                    "id": e.id,
                    "filename": e.filename,
                    "format": e.format,
                    "file_size_bytes": e.file_size_bytes,
                    "reason": e.reason,
                    "created_at": e.created_at.isoformat(),
                }
                for e in session.query(QuarantineEntry)
                .order_by(QuarantineEntry.created_at)
                .all()
            ]
        finally:
            session.close()

    def get_quarantine(self, entry_id: str) -> Optional[Dict[str, Any]]:
        session = self._session()
        try:
            e = session.get(QuarantineEntry, entry_id)
            if e is None:
                return None
            return {
                "id": e.id,
                "filename": e.filename,
                "format": e.format,
                "file_size_bytes": e.file_size_bytes,
                "reason": e.reason,
                "content_b64": e.content_b64,
                "created_at": e.created_at.isoformat(),
            }
        finally:
            session.close()

    def remove_quarantine(self, entry_id: str) -> bool:
        session = self._session()
        try:
            e = session.get(QuarantineEntry, entry_id)
            if e is None:
                return False
            session.delete(e)
            session.commit()
            return True
        finally:
            session.close()


def _job_dict(job: ProcessingJob) -> Dict[str, Any]:
    return {
        "id": job.id,
        "filename": job.filename,
        "status": job.status,
        "document_id": job.document_id,
        "total_chunks": job.total_chunks,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
    }
