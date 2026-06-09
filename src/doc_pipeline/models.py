from pgvector.sqlalchemy import Vector
from shared_core.database import Base, TimestampMixin, UUIDMixin
from sqlalchemy import Column, ForeignKey, Integer, String, Text


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    filename = Column(String(500), nullable=False)
    format = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)


class Chunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chunks"

    document_id = Column(
        String(36), ForeignKey("documents.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    embedding = Column(Vector(1536), nullable=True)
