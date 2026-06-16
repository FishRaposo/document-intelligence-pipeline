"""Metadata extraction tests."""

from doc_pipeline.metadata import extract_metadata
from doc_pipeline.parsers import DocumentParser


def _parse(data: bytes, name: str):
    return DocumentParser().parse(data, name)


class TestMetadata:
    def test_title_from_markdown_heading(self, sample_md_bytes):
        parsed = _parse(sample_md_bytes, "report.md")
        meta = extract_metadata(parsed, "report.md", len(sample_md_bytes))
        assert meta["title"] == "Quantum Computing Report"

    def test_author_extracted(self, sample_md_bytes):
        parsed = _parse(sample_md_bytes, "report.md")
        meta = extract_metadata(parsed, "report.md")
        assert meta["author"] == "Dr. Jane Smith"

    def test_dates_extracted(self, sample_md_bytes):
        parsed = _parse(sample_md_bytes, "report.md")
        meta = extract_metadata(parsed, "report.md")
        assert "2024-01-15" in meta["dates"]

    def test_word_and_char_counts(self):
        parsed = _parse(b"one two three four five", "x.txt")
        meta = extract_metadata(parsed, "x.txt", 23)
        assert meta["word_count"] == 5
        assert meta["char_count"] == len("one two three four five")
        assert meta["file_size_bytes"] == 23

    def test_title_falls_back_to_filename(self):
        parsed = _parse(b"", "empty.txt")
        meta = extract_metadata(parsed, "empty.txt")
        assert meta["title"] == "empty.txt"

    def test_dates_deduplicated(self):
        parsed = _parse(b"2024-01-01 and again 2024-01-01 and 2025-02-02", "d.txt")
        meta = extract_metadata(parsed, "d.txt")
        assert meta["dates"] == ["2024-01-01", "2025-02-02"]

    def test_various_date_formats(self):
        text = b"Dated 31 Jan 2024 and also January 5, 2023 here."
        parsed = _parse(text, "d.txt")
        meta = extract_metadata(parsed, "d.txt")
        assert any("2024" in d for d in meta["dates"])
        assert any("2023" in d for d in meta["dates"])
