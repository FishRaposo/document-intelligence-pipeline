"""JSONL exporter and RAG-record shaping tests."""

import json
import os
import tempfile

from doc_pipeline.exporters import JSONLExporter, to_rag_records


class TestJSONLExporter:
    def test_export_writes_jsonl(self, sample_chunks):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tmp:
            path = tmp.name
        try:
            JSONLExporter(path).export(sample_chunks)
            with open(path, encoding="utf-8") as f:
                lines = f.read().strip().split("\n")
            assert len(lines) == 2
            assert json.loads(lines[0])["content"] == "first chunk"
        finally:
            os.unlink(path)

    def test_export_empty(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tmp:
            path = tmp.name
        try:
            JSONLExporter(path).export([])
            with open(path, encoding="utf-8") as f:
                assert f.read() == ""
        finally:
            os.unlink(path)

    def test_dumps_string(self, sample_chunks):
        body = JSONLExporter().dumps(sample_chunks)
        assert len(body.splitlines()) == 2
        assert json.loads(body.splitlines()[1])["chunk_id"] == 1

    def test_export_unicode(self):
        chunks = [{"chunk_id": 0, "content": "snowman ☃", "word_count": 2}]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tmp:
            path = tmp.name
        try:
            JSONLExporter(path).export(chunks)
            with open(path, encoding="utf-8") as f:
                assert "☃" in json.loads(f.readline())["content"]
        finally:
            os.unlink(path)


class TestRagRecords:
    def test_shapes_records(self):
        doc = {"id": "doc1", "filename": "f.md", "title": "T"}
        chunks = [
            {"chunk_index": 0, "content": "first", "word_count": 1},
            {"chunk_index": 1, "content": "second", "word_count": 1},
        ]
        records = to_rag_records(doc, chunks)
        assert records[0]["id"] == "doc1:0"
        assert records[0]["text"] == "first"
        assert records[0]["metadata"]["filename"] == "f.md"
        assert records[1]["metadata"]["chunk_index"] == 1
