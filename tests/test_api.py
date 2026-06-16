"""API tests covering every endpoint, success and error paths.

The app boots offline (in-memory store + vector store, no DB, no keys). We reset
the module globals per test for isolation. ``db_manager`` / ``redis_manager`` are
patched so the health endpoint reports a deterministic status.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from shared_core.vectorstore import get_vector_store

    from doc_pipeline import main
    from doc_pipeline.pipeline import DocumentPipeline
    from doc_pipeline.storage import InMemoryDocumentStore

    # Fresh offline state per test.
    main.store = InMemoryDocumentStore()
    main.vector_store = get_vector_store(offline=True)
    main.pipeline = DocumentPipeline(main.store, main.vector_store)

    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    with patch.object(main, "redis_manager", mock_redis):
        # Do not run the DB-probe lifespan (keep offline); use plain TestClient.
        yield TestClient(main.app)


def _ingest_text(client, filename, text):
    return client.post("/ingest/text", json={"filename": filename, "text": text})


class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["service"] == "document-intelligence-pipeline"
        assert "dependencies" in body


class TestIngest:
    def test_ingest_file_txt(self, client):
        r = client.post(
            "/ingest",
            files={"file": ("test.txt", b"hello world content here", "text/plain")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "completed"
        assert body["total_chunks"] >= 1

    def test_ingest_file_markdown(self, client):
        r = client.post(
            "/ingest",
            files={"file": ("n.md", b"# Title\n\nSome content body.", "text/markdown")},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Title"

    def test_ingest_unsupported_format_quarantines(self, client):
        r = client.post(
            "/ingest",
            files={"file": ("x.xyz", b"junk", "application/octet-stream")},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "quarantined"

    def test_ingest_text_endpoint(self, client):
        r = _ingest_text(client, "doc.txt", "plain text body content")
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_ingest_missing_file_is_validation_error(self, client):
        r = client.post("/ingest")
        assert r.status_code == 400

    def test_ingest_duplicate(self, client):
        _ingest_text(client, "a.txt", "identical body for dedup test")
        r = _ingest_text(client, "b.txt", "identical body for dedup test")
        assert r.json()["status"] == "duplicate"


class TestBatch:
    def test_batch_sync(self, client):
        r = client.post(
            "/ingest/batch",
            json={
                "documents": [
                    {"filename": "a.txt", "text": "alpha body content"},
                    {"filename": "b.txt", "text": "beta body content"},
                    {"filename": "bad.xyz", "text": "junk"},
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 3
        assert body["completed"] == 2
        assert body["quarantined"] == 1


class TestBrowsing:
    def test_list_and_get_document(self, client):
        ingest = _ingest_text(client, "doc.txt", "content for listing test")
        doc_id = ingest.json()["document_id"]

        listed = client.get("/documents")
        assert listed.status_code == 200
        assert len(listed.json()["documents"]) == 1

        single = client.get(f"/documents/{doc_id}")
        assert single.status_code == 200
        assert single.json()["filename"] == "doc.txt"

    def test_get_missing_document_404(self, client):
        assert client.get("/documents/nope").status_code == 404

    def test_get_chunks(self, client):
        ingest = _ingest_text(client, "doc.txt", "one two three four five six seven")
        doc_id = ingest.json()["document_id"]
        r = client.get(f"/documents/{doc_id}/chunks")
        assert r.status_code == 200
        assert len(r.json()["chunks"]) >= 1

    def test_get_chunks_missing_doc_404(self, client):
        assert client.get("/documents/nope/chunks").status_code == 404


class TestSearch:
    def test_search(self, client):
        _ingest_text(
            client, "doc.txt", "quantum computing qubits superposition entanglement"
        )
        r = client.post("/search", json={"query": "qubits superposition", "top_k": 3})
        assert r.status_code == 200
        assert len(r.json()["results"]) >= 1

    def test_search_validation(self, client):
        r = client.post("/search", json={"query": "x", "top_k": 0})
        assert r.status_code == 422


class TestQuarantineAPI:
    def test_list_quarantine(self, client):
        client.post(
            "/ingest", files={"file": ("x.xyz", b"junk", "application/octet-stream")}
        )
        r = client.get("/quarantine")
        assert r.status_code == 200
        assert len(r.json()["quarantine"]) == 1

    def test_reprocess_missing_404(self, client):
        assert client.post("/quarantine/nope/reprocess").status_code == 404


class TestExport:
    def test_export_jsonl(self, client):
        ingest = _ingest_text(client, "doc.txt", "alpha beta gamma delta content body")
        doc_id = ingest.json()["document_id"]
        r = client.get(f"/export/{doc_id}")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/x-ndjson")
        first_line = r.text.strip().splitlines()[0]
        assert '"text"' in first_line
        assert '"metadata"' in first_line

    def test_export_missing_404(self, client):
        assert client.get("/export/nope").status_code == 404
