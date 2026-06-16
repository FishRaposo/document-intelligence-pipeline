"""Schema/model tests for documents, chunks, processing jobs, and quarantine."""

from doc_pipeline.models import Chunk, Document, ProcessingJob, QuarantineEntry


class TestDocumentModel:
    def test_columns(self):
        for col in (
            "filename",
            "format",
            "file_size_bytes",
            "total_chunks",
            "content_hash",
            "title",
            "author",
            "word_count",
            "doc_metadata",
            "entities",
            "id",
            "created_at",
            "updated_at",
        ):
            assert hasattr(Document, col)

    def test_tablename(self):
        assert Document.__tablename__ == "documents"

    def test_content_hash_unique_indexed(self):
        col = Document.__table__.columns["content_hash"]
        assert col.index is True
        assert col.unique is True


class TestChunkModel:
    def test_columns(self):
        for col in (
            "document_id",
            "chunk_index",
            "content",
            "word_count",
            "content_hash",
            "embedding",
        ):
            assert hasattr(Chunk, col)

    def test_tablename(self):
        assert Chunk.__tablename__ == "chunks"

    def test_document_id_indexed(self):
        assert Chunk.__table__.columns["document_id"].index is True


class TestProcessingJobModel:
    def test_columns_and_tablename(self):
        assert ProcessingJob.__tablename__ == "processing_jobs"
        for col in ("filename", "status", "document_id", "total_chunks", "error"):
            assert hasattr(ProcessingJob, col)

    def test_status_indexed(self):
        assert ProcessingJob.__table__.columns["status"].index is True


class TestQuarantineModel:
    def test_columns_and_tablename(self):
        assert QuarantineEntry.__tablename__ == "quarantine"
        for col in ("filename", "format", "reason", "content_b64"):
            assert hasattr(QuarantineEntry, col)
