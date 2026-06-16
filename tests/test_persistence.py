"""Pipeline persistence against a SQLite-backed store (no real PostgreSQL).

Exercises the default DB persistence path end-to-end using
``shared_core.testing.MockDatabase`` for the relational store and an in-memory
vector store for search.
"""

from shared_core.testing import MockDatabase
from shared_core.vectorstore import get_vector_store

from doc_pipeline.pipeline import DocumentPipeline
from doc_pipeline.storage_db import DatabaseDocumentStore


def _db_pipeline():
    mock_db = MockDatabase()
    store = DatabaseDocumentStore(mock_db.get_session)
    vector_store = get_vector_store(offline=True)
    return DocumentPipeline(store, vector_store), store


class TestPersistence:
    def test_ingest_persists_to_db_store(self, sample_md_bytes):
        pipeline, store = _db_pipeline()
        result = pipeline.ingest(sample_md_bytes, "report.md")
        assert result.status == "completed"
        # survives via the store (re-read from the DB rows)
        doc = store.get_document(result.document_id)
        assert doc["filename"] == "report.md"
        assert len(store.get_chunks(result.document_id)) == result.total_chunks

    def test_get_document_includes_file_size_bytes(self, sample_md_bytes):
        # get_document must expose file_size_bytes (parity with the in-memory
        # store and the TS DocumentDetail type).
        pipeline, store = _db_pipeline()
        result = pipeline.ingest(sample_md_bytes, "report.md")
        doc = store.get_document(result.document_id)
        assert doc["file_size_bytes"] == len(sample_md_bytes)

    def test_dedup_persists_once(self, sample_md_bytes):
        pipeline, store = _db_pipeline()
        pipeline.ingest(sample_md_bytes, "a.md")
        dup = pipeline.ingest(sample_md_bytes, "b.md")
        assert dup.status == "duplicate"
        assert len(store.list_documents()) == 1

    def test_quarantine_persists(self):
        pipeline, store = _db_pipeline()
        pipeline.ingest(b"junk", "bad.xyz")
        assert len(store.list_quarantine()) == 1

    def test_search_after_db_ingest(self, sample_md_bytes):
        pipeline, _ = _db_pipeline()
        pipeline.ingest(sample_md_bytes, "report.md")
        hits = pipeline.search("qubits information retrieval", top_k=2)
        assert len(hits) >= 1
