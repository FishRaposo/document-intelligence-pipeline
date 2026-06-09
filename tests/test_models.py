from doc_pipeline.models import Chunk, Document


class TestDocumentModel:
    def test_document_has_expected_columns(self):
        assert hasattr(Document, "filename")
        assert hasattr(Document, "format")
        assert hasattr(Document, "file_size_bytes")
        assert hasattr(Document, "total_chunks")
        assert hasattr(Document, "id")
        assert hasattr(Document, "created_at")
        assert hasattr(Document, "updated_at")

    def test_document_tablename(self):
        assert Document.__tablename__ == "documents"


class TestChunkModel:
    def test_chunk_has_expected_columns(self):
        assert hasattr(Chunk, "document_id")
        assert hasattr(Chunk, "chunk_index")
        assert hasattr(Chunk, "content")
        assert hasattr(Chunk, "word_count")
        assert hasattr(Chunk, "embedding")
        assert hasattr(Chunk, "id")
        assert hasattr(Chunk, "created_at")
        assert hasattr(Chunk, "updated_at")

    def test_chunk_tablename(self):
        assert Chunk.__tablename__ == "chunks"

    def test_chunk_document_id_is_indexed(self):
        col = Chunk.__table__.columns["document_id"]
        assert col.index is True
