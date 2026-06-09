import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from .models import Chunk, Document


class DatabaseDocumentStorage:
    """PostgreSQL-backed document and chunk persistence."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save_document(
        self,
        filename: str,
        file_format: str,
        file_size: int,
        chunks: List[Dict[str, Any]],
    ) -> str:
        doc_id = str(uuid.uuid4())
        session: Session = next(self.session_factory())
        try:
            doc = Document(
                id=doc_id,
                filename=filename,
                format=file_format,
                file_size_bytes=file_size,
                total_chunks=len(chunks),
            )
            session.add(doc)
            for i, ch in enumerate(chunks):
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    chunk_index=i,
                    content=ch.get("content", ""),
                    word_count=ch.get("word_count", 0),
                    embedding=ch.get("embedding"),
                )
                session.add(chunk)
            session.commit()
            logger.info(f"Saved document {doc_id} with {len(chunks)} chunks")
            return doc_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save document: {e}")
            raise
        finally:
            session.close()

    def get_document(self, doc_id: str) -> Optional[Dict]:
        session: Session = next(self.session_factory())
        try:
            doc = session.get(Document, doc_id)
            if not doc:
                return None
            return {
                "id": doc.id,
                "filename": doc.filename,
                "format": doc.format,
                "total_chunks": doc.total_chunks,
                "created_at": doc.created_at.isoformat(),
            }
        finally:
            session.close()

    def get_chunks(self, doc_id: str) -> List[Dict]:
        session: Session = next(self.session_factory())
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
