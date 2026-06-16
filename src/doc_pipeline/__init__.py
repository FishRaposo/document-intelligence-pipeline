"""Document Intelligence Pipeline.

A multi-stage ingestion pipeline that turns raw files into clean, deduplicated,
semantically chunked, vector-embedded, RAG-ready knowledge — built on
``shared_core`` (docparse, embeddings, vectorstore, database, tasks).
"""

__version__ = "1.0.0"

from .chunkers import Chunker, ChunkError, SlidingWindowChunker
from .cleaners import clean_extracted_text
from .config import AppConfig
from .dedup import content_hash, dedup_chunks
from .embeddings import EmbeddingError, EmbeddingGenerator, MockEmbeddingGenerator
from .entities import extract_entities
from .exporters import JSONLExporter, to_rag_records
from .metadata import extract_metadata
from .parsers import DocumentParser, ParseError
from .pipeline import DocumentPipeline, IngestResult
from .storage import InMemoryDocumentStore

__all__ = [
    "AppConfig",
    "ChunkError",
    "Chunker",
    "DocumentParser",
    "DocumentPipeline",
    "EmbeddingError",
    "EmbeddingGenerator",
    "InMemoryDocumentStore",
    "IngestResult",
    "JSONLExporter",
    "MockEmbeddingGenerator",
    "ParseError",
    "SlidingWindowChunker",
    "clean_extracted_text",
    "content_hash",
    "dedup_chunks",
    "extract_entities",
    "extract_metadata",
    "to_rag_records",
]
