"""The end-to-end ingestion pipeline.

Orchestrates the full flow for one document:

    parse -> clean -> extract metadata + entities -> chunk -> dedup chunks ->
    embed -> persist (store) -> index vectors (vector store)

Failures are caught and recorded in the *quarantine* so a bad file never aborts a
batch and can be reprocessed later. The pipeline is store- and vector-store-
agnostic: it receives both via the constructor, so the same code runs against the
in-memory backends (tests/demo) or PostgreSQL + pgvector (production).
"""

import base64
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger
from shared_core.docparse import ChunkStrategy
from shared_core.vectorstore import VectorRecord, VectorStore

from .chunkers import Chunker
from .cleaners import clean_extracted_text
from .dedup import content_hash, dedup_chunks
from .embeddings import EmbeddingGenerator
from .entities import extract_entities
from .metadata import extract_metadata
from .parsers import DocumentParser, ParseError


@dataclass
class IngestResult:
    """Outcome of ingesting a single document."""

    status: str  # "completed" | "duplicate" | "quarantined"
    filename: str
    document_id: Optional[str] = None
    total_chunks: int = 0
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    entities: Dict[str, Any] = field(default_factory=dict)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    quarantine_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "filename": self.filename,
            "document_id": self.document_id,
            "total_chunks": self.total_chunks,
            "title": self.title,
            "metadata": self.metadata,
            "entities": self.entities,
            "chunks": self.chunks,
            "error": self.error,
            "quarantine_id": self.quarantine_id,
        }


class DocumentPipeline:
    """Runs the ingestion pipeline against a document store and vector store."""

    def __init__(
        self,
        store: Any,
        vector_store: VectorStore,
        *,
        embedder: Optional[EmbeddingGenerator] = None,
        chunker: Optional[Chunker] = None,
        parser: Optional[DocumentParser] = None,
        vector_namespace: str = "chunks",
    ):
        self.store = store
        self.vector_store = vector_store
        self.parser = parser or DocumentParser()
        self.chunker = chunker or Chunker(strategy=ChunkStrategy.SEMANTIC)
        self.embedder = embedder or EmbeddingGenerator(offline=True)
        self.vector_namespace = vector_namespace

    def ingest(self, content: bytes, filename: str) -> IngestResult:
        """Ingest one document; never raises — failures are quarantined."""
        file_format = self.parser.file_format(filename)
        file_size = len(content)
        try:
            parsed = self.parser.parse(content, filename)
        except ParseError as exc:
            return self._quarantine(content, filename, file_format, file_size, str(exc))
        except Exception as exc:  # noqa: BLE001 - defensive: quarantine anything
            logger.exception("Unexpected parse failure for {}", filename)
            return self._quarantine(
                content, filename, file_format, file_size, f"parse error: {exc}"
            )

        cleaned = clean_extracted_text(parsed.text)
        doc_hash = content_hash(cleaned)

        existing_id = self.store.find_by_hash(doc_hash)
        if existing_id is not None:
            logger.info("Duplicate document '{}' -> {}", filename, existing_id)
            return IngestResult(
                status="duplicate",
                filename=filename,
                document_id=existing_id,
            )

        metadata = extract_metadata(parsed, filename, file_size)
        entities = extract_entities(cleaned)

        chunks = self.chunker.chunk_text(cleaned)
        chunks = dedup_chunks(chunks)
        for chunk in chunks:
            chunk["content_hash"] = content_hash(chunk["content"])
        self.embedder.embed_chunks(chunks)

        doc_id = self.store.save_document(
            filename=filename,
            file_format=file_format,
            file_size=file_size,
            content_hash=doc_hash,
            chunks=chunks,
            metadata=metadata,
            entities=entities,
        )
        self._index_vectors(doc_id, filename, chunks)

        return IngestResult(
            status="completed",
            filename=filename,
            document_id=doc_id,
            total_chunks=len(chunks),
            title=metadata.get("title"),
            metadata=metadata,
            entities=entities,
            chunks=[
                {
                    "chunk_id": c["chunk_id"],
                    "content": c["content"],
                    "word_count": c["word_count"],
                }
                for c in chunks
            ],
        )

    def _index_vectors(
        self, doc_id: str, filename: str, chunks: List[Dict[str, Any]]
    ) -> None:
        records = [
            VectorRecord(
                id=f"{doc_id}:{c['chunk_id']}",
                vector=c.get("embedding") or [],
                payload={
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_id": c["chunk_id"],
                    "content": c["content"],
                },
            )
            for c in chunks
            if c.get("embedding")
        ]
        if records:
            self.vector_store.add_many(records)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Embed ``query`` and return the top-k most similar stored chunks."""
        query_vector = self.embedder.embed_text(query)
        hits = self.vector_store.query(query_vector, top_k=top_k)
        return [
            {
                "id": hit.id,
                "score": round(hit.score, 6),
                "document_id": hit.payload.get("document_id"),
                "filename": hit.payload.get("filename"),
                "chunk_id": hit.payload.get("chunk_id"),
                "content": hit.payload.get("content"),
            }
            for hit in hits
        ]

    def _quarantine(
        self,
        content: bytes,
        filename: str,
        file_format: str,
        file_size: int,
        reason: str,
    ) -> IngestResult:
        logger.warning("Quarantining '{}': {}", filename, reason)
        encoded = base64.b64encode(content).decode("ascii") if content else None
        entry_id = self.store.quarantine(
            filename=filename,
            reason=reason,
            file_format=file_format,
            file_size=file_size,
            content_b64=encoded,
        )
        return IngestResult(
            status="quarantined",
            filename=filename,
            error=reason,
            quarantine_id=entry_id,
        )

    def reprocess_quarantine(self, entry_id: str) -> Optional[IngestResult]:
        """Re-run ingestion for a quarantined entry; removes it on success."""
        entry = self.store.get_quarantine(entry_id)
        if entry is None:
            return None
        content = (
            base64.b64decode(entry["content_b64"]) if entry.get("content_b64") else b""
        )
        result = self.ingest(content, entry["filename"])
        if result.status in {"completed", "duplicate"}:
            self.store.remove_quarantine(entry_id)
        elif result.status == "quarantined" and result.quarantine_id is not None:
            # Still unparseable: drop the newly-created duplicate entry so that
            # reprocessing a permanently-broken file is idempotent (the original
            # entry stays; the count does not grow on each retry).
            self.store.remove_quarantine(result.quarantine_id)
            result.quarantine_id = entry_id
        return result
