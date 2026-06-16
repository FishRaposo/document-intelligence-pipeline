"""Tests for the in-memory and database-backed document stores.

The database path runs against an in-memory SQLite via
``shared_core.testing.MockDatabase`` — no real PostgreSQL required. Both stores
expose the same interface, so the same assertions run against either backend.
"""

import pytest
from shared_core.testing import MockDatabase

from doc_pipeline.storage import InMemoryDocumentStore
from doc_pipeline.storage_db import DatabaseDocumentStore

CHUNKS = [
    {
        "content": "alpha beta",
        "word_count": 2,
        "content_hash": "h0",
        "embedding": [0.1],
    },
    {
        "content": "gamma delta",
        "word_count": 2,
        "content_hash": "h1",
        "embedding": [0.2],
    },
]
META = {"title": "T", "author": "A", "word_count": 4}
ENTS = {"emails": ["x@y.com"], "urls": [], "phones": [], "capitalised": []}


@pytest.fixture(params=["memory", "db"])
def doc_store(request):
    if request.param == "memory":
        return InMemoryDocumentStore()
    mock_db = MockDatabase()
    return DatabaseDocumentStore(mock_db.get_session)


class TestDocumentStore:
    def test_save_and_get_document(self, doc_store):
        doc_id = doc_store.save_document(
            filename="f.md",
            file_format="md",
            file_size=10,
            content_hash="dochash",
            chunks=CHUNKS,
            metadata=META,
            entities=ENTS,
        )
        doc = doc_store.get_document(doc_id)
        assert doc["filename"] == "f.md"
        assert doc["total_chunks"] == 2
        assert doc["title"] == "T"

    def test_get_chunks_ordered(self, doc_store):
        doc_id = doc_store.save_document(
            filename="f.md",
            file_format="md",
            file_size=10,
            content_hash="h",
            chunks=CHUNKS,
            metadata=META,
        )
        chunks = doc_store.get_chunks(doc_id)
        assert [c["chunk_index"] for c in chunks] == [0, 1]
        assert chunks[0]["content"] == "alpha beta"

    def test_dedup_on_hash(self, doc_store):
        kw = {
            "filename": "f.md",
            "file_format": "md",
            "file_size": 1,
            "chunks": CHUNKS,
            "metadata": META,
        }
        a = doc_store.save_document(content_hash="same", **kw)
        b = doc_store.save_document(content_hash="same", **kw)
        assert a == b
        assert len(doc_store.list_documents()) == 1

    def test_find_by_hash(self, doc_store):
        doc_id = doc_store.save_document(
            filename="f.md",
            file_format="md",
            file_size=1,
            content_hash="findme",
            chunks=[],
            metadata=META,
        )
        assert doc_store.find_by_hash("findme") == doc_id
        assert doc_store.find_by_hash("absent") is None

    def test_list_documents(self, doc_store):
        for i in range(3):
            doc_store.save_document(
                filename=f"f{i}.md",
                file_format="md",
                file_size=1,
                content_hash=f"h{i}",
                chunks=[],
                metadata=META,
            )
        assert len(doc_store.list_documents()) == 3

    def test_missing_document_returns_none(self, doc_store):
        assert doc_store.get_document("nope") is None


class TestJobs:
    def test_job_lifecycle(self, doc_store):
        job_id = doc_store.create_job("f.md")
        assert doc_store.get_job(job_id)["status"] == "queued"
        doc_store.update_job(job_id, status="completed", total_chunks=3)
        job = doc_store.get_job(job_id)
        assert job["status"] == "completed"
        assert job["total_chunks"] == 3
        assert any(j["id"] == job_id for j in doc_store.list_jobs())


class TestQuarantineStore:
    def test_quarantine_and_list(self, doc_store):
        entry_id = doc_store.quarantine(
            filename="bad.xyz",
            reason="Unsupported format",
            file_format="xyz",
            file_size=5,
            content_b64="YmFk",
        )
        listed = doc_store.list_quarantine()
        assert len(listed) == 1
        assert listed[0]["filename"] == "bad.xyz"
        # content_b64 is not in the list projection
        assert "content_b64" not in listed[0]
        full = doc_store.get_quarantine(entry_id)
        assert full["content_b64"] == "YmFk"

    def test_remove_quarantine(self, doc_store):
        entry_id = doc_store.quarantine(filename="bad.xyz", reason="x")
        assert doc_store.remove_quarantine(entry_id) is True
        assert doc_store.remove_quarantine(entry_id) is False
        assert doc_store.list_quarantine() == []
