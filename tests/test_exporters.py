import json
import os
import tempfile

from doc_pipeline.exporters import JSONLExporter


class TestJSONLExporter:
    def test_export_writes_jsonl(self, sample_chunks):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".jsonl"
        ) as tmp:
            path = tmp.name

        try:
            exporter = JSONLExporter(path)
            exporter.export(sample_chunks)

            with open(path, encoding="utf-8") as f:
                lines = f.read().strip().split("\n")

            assert len(lines) == 2
            parsed = [json.loads(line) for line in lines]
            assert parsed[0]["chunk_id"] == 0
            assert parsed[0]["content"] == "first chunk"
            assert parsed[1]["chunk_id"] == 1
        finally:
            os.unlink(path)

    def test_export_empty_list(self):
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".jsonl"
        ) as tmp:
            path = tmp.name

        try:
            exporter = JSONLExporter(path)
            exporter.export([])

            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert content == ""
        finally:
            os.unlink(path)

    def test_export_special_characters(self):
        chunks = [
            {
                "chunk_id": 0,
                "content": 'unicode: \u2603 \u00f1 "quotes"',
                "word_count": 5,
            }
        ]
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".jsonl"
        ) as tmp:
            path = tmp.name

        try:
            exporter = JSONLExporter(path)
            exporter.export(chunks)

            with open(path, encoding="utf-8") as f:
                line = f.readline().strip()
            parsed = json.loads(line)
            assert "\u2603" in parsed["content"]
        finally:
            os.unlink(path)
