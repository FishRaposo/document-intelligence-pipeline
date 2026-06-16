"""SQLAlchemy models for documents, chunks, processing jobs, and quarantine.

These tables back the default PostgreSQL persistence path. To keep the schema
testable on SQLite (the offline in-memory fallback used by tests and the demo),
chunk embeddings are stored as JSON rather than a native ``pgvector`` column —
the vector *search* path lives in ``shared_core.vectorstore`` (in-memory by
default, pgvector when a database is configured), so the relational store does
not need a vector column to function.
"""

from shared_core.database import Base, TimestampMixin, UUIDMixin
from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text


class Document(Base, UUIDMixin, TimestampMixin):
    """An ingested source document and its extracted metadata."""

    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    format = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    content_hash = Column(String(64), nullable=False, index=True, unique=True)
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    word_count = Column(Integer, default=0)
    doc_metadata = Column(JSON, nullable=True)
    entities = Column(JSON, nullable=True)


class Chunk(Base, UUIDMixin, TimestampMixin):
    """A semantically chunked slice of a document, with its embedding vector."""

    __tablename__ = "chunks"

    document_id = Column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    content_hash = Column(String(64), nullable=True, index=True)
    embedding = Column(JSON, nullable=True)


class ProcessingJob(Base, UUIDMixin, TimestampMixin):
    """Tracks an ingestion job through its lifecycle.

    ``status`` transitions: queued -> processing -> completed | failed.
    """

    __tablename__ = "processing_jobs"

    filename = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="queued", index=True)
    document_id = Column(String(36), nullable=True)
    total_chunks = Column(Integer, default=0)
    error = Column(Text, nullable=True)


class QuarantineEntry(Base, UUIDMixin, TimestampMixin):
    """A document that failed parsing/processing, retained for reprocessing."""

    __tablename__ = "quarantine"

    filename = Column(String(500), nullable=False)
    format = Column(String(20), nullable=True)
    file_size_bytes = Column(Integer, default=0)
    reason = Column(Text, nullable=False)
    content_b64 = Column(Text, nullable=True)
