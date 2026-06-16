"""Worker tests — the pure task logic runs with NO broker and NO database.

The Celery app is importable without a broker; we test the underlying
``_process_one`` / ``_process_batch`` helpers (offline, in-memory backends).
"""

import base64

from doc_pipeline import worker


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class TestWorker:
    def test_celery_app_importable(self):
        assert worker.celery_app is not None
        assert worker.process_document_task.name == "doc_pipeline.process_document"
        assert worker.batch_ingest_task.name == "doc_pipeline.batch_ingest"

    def test_process_one_completes(self):
        result = worker._process_one("doc.txt", _b64("hello world from worker"))
        assert result["status"] == "completed"
        assert result["total_chunks"] >= 1

    def test_process_one_quarantines_bad_format(self):
        result = worker._process_one("bad.xyz", _b64("data"))
        assert result["status"] == "quarantined"

    def test_process_batch_mixed(self):
        docs = [
            {"filename": "a.txt", "content_b64": _b64("alpha document content")},
            {"filename": "b.txt", "content_b64": _b64("beta document content")},
            {"filename": "bad.xyz", "content_b64": _b64("junk")},
        ]
        summary = worker._process_batch(docs)
        assert summary["total"] == 3
        assert summary["completed"] == 2
        assert summary["quarantined"] == 1
        assert len(summary["results"]) == 3

    def test_process_batch_dedups(self):
        same = _b64("the very same document body across two entries")
        docs = [
            {"filename": "a.txt", "content_b64": same},
            {"filename": "b.txt", "content_b64": same},
        ]
        summary = worker._process_batch(docs)
        assert summary["completed"] == 1
        assert summary["duplicates"] == 1
