"""Parser tests — built on ``shared_core.docparse`` via ``DocumentParser``.

Plain text / Markdown / HTML run with the installed optional deps; PDF and DOCX
are exercised behind ``importorskip`` so the suite stays green with no heavy deps.
"""

import pytest

from doc_pipeline.parsers import DocumentParser, ParseError


class TestDocumentParser:
    def test_parse_txt(self, sample_txt_bytes):
        parser = DocumentParser()
        parsed = parser.parse(sample_txt_bytes, "test.txt")
        assert "sample text document" in parsed.text
        assert "multiple lines" in parsed.text

    def test_parse_bytes_returns_text(self, sample_txt_bytes):
        parser = DocumentParser()
        text = parser.parse_bytes(sample_txt_bytes, "test.txt")
        assert isinstance(text, str)
        assert "sample text document" in text

    def test_parse_md_extracts_title(self, sample_md_bytes):
        parser = DocumentParser()
        parsed = parser.parse(sample_md_bytes, "report.md")
        assert parsed.title == "Quantum Computing Report"
        assert "qubits" in parsed.text

    def test_parse_html_strips_scripts(self, sample_html_bytes):
        parser = DocumentParser()
        parsed = parser.parse(sample_html_bytes, "page.html")
        assert "Paragraph one has content" in parsed.text
        assert "console.log" not in parsed.text
        assert parsed.title == "HTML Doc"

    def test_parse_htm_extension(self, sample_html_bytes):
        parser = DocumentParser()
        parsed = parser.parse(sample_html_bytes, "page.htm")
        assert "Heading" in parsed.text

    def test_unsupported_format_raises_parse_error(self):
        parser = DocumentParser()
        with pytest.raises(ParseError, match="Unsupported format"):
            parser.parse(b"dummy", "file.xyz")

    def test_parse_error_carries_filename(self):
        parser = DocumentParser()
        with pytest.raises(ParseError) as exc:
            parser.parse(b"dummy", "bad.xyz")
        assert exc.value.filename == "bad.xyz"

    def test_empty_txt(self):
        parser = DocumentParser()
        parsed = parser.parse(b"", "empty.txt")
        assert parsed.text == ""

    def test_file_format_helper(self):
        assert DocumentParser.file_format("a.PDF") == "pdf"
        assert DocumentParser.file_format("a.md") == "md"
        assert DocumentParser.file_format("noext") == ""

    def test_parse_file_from_disk(self, tmp_path):
        path = tmp_path / "doc.txt"
        path.write_text("hello from disk", encoding="utf-8")
        parser = DocumentParser()
        assert "hello from disk" in parser.parse_file(str(path))


class TestOptionalFormats:
    def test_parse_pdf_when_pymupdf_available(self):
        fitz = pytest.importorskip("fitz")
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello PDF world")
        data = doc.tobytes()
        doc.close()

        parser = DocumentParser()
        parsed = parser.parse(data, "doc.pdf")
        assert "Hello PDF world" in parsed.text
        assert parsed.page_count == 1

    def test_parse_docx_when_python_docx_available(self):
        docx = pytest.importorskip("docx")
        import io

        document = docx.Document()
        document.add_paragraph("First paragraph in docx.")
        document.add_paragraph("Second paragraph here.")
        buffer = io.BytesIO()
        document.save(buffer)

        parser = DocumentParser()
        parsed = parser.parse(buffer.getvalue(), "doc.docx")
        assert "First paragraph in docx" in parsed.text
