import pytest
from doc_pipeline.parsers import DocumentParser, ParseError


class TestDocumentParser:
    def test_parse_bytes_txt(self, sample_txt_bytes):
        parser = DocumentParser()
        result = parser.parse_bytes(sample_txt_bytes, "test.txt")
        assert "sample text document" in result
        assert "multiple lines" in result

    def test_parse_bytes_md(self, sample_md_bytes):
        parser = DocumentParser()
        result = parser.parse_bytes(sample_md_bytes, "test.md")
        assert "Heading One" in result
        assert "bold" in result
        assert "italic" in result
        assert "link" not in result.lower() or "Link text" in result
        assert "blockquote" in result

    def test_parse_bytes_html(self, sample_html_bytes):
        parser = DocumentParser()
        result = parser.parse_bytes(sample_html_bytes, "test.html")
        assert "Title" in result
        assert "Paragraph text here" in result
        assert "console.log" not in result

    def test_parse_bytes_unsupported_format(self):
        parser = DocumentParser()
        with pytest.raises(ParseError, match="Unsupported format"):
            parser.parse_bytes(b"dummy", "test.xyz")

    def test_parse_bytes_empty_txt(self):
        parser = DocumentParser()
        result = parser.parse_bytes(b"", "empty.txt")
        assert result == ""

    def test_parse_bytes_html_no_bs4(self, monkeypatch):
        parser = DocumentParser()
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "bs4":
                raise ImportError("No bs4")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        result = parser.parse_bytes(
            b"<html><body>Simple text</body></html>", "test.html"
        )
        assert "Simple text" in result

    def test_parse_bytes_pdf_requires_pdfplumber(self, monkeypatch):
        parser = DocumentParser()
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("No pdfplumber")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ParseError, match="pdfplumber"):
            parser.parse_bytes(b"%PDF-1.4\n...", "test.pdf")

    def test_parse_bytes_docx_requires_python_docx(self, monkeypatch):
        parser = DocumentParser()
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "docx":
                raise ImportError("No docx")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ParseError, match="python-docx"):
            parser.parse_bytes(b"PK\x03\x04", "test.docx")

    def test_parse_bytes_with_htm_extension(self, sample_html_bytes):
        parser = DocumentParser()
        result = parser.parse_bytes(sample_html_bytes, "test.htm")
        assert "Title" in result

    def test_parse_error_has_filename(self):
        parser = DocumentParser()
        with pytest.raises(ParseError) as exc_info:
            parser.parse_bytes(b"dummy", "bad.xyz")
        assert exc_info.value.filename == "bad.xyz"

    def test_parse_md_strips_headers(self):
        parser = DocumentParser()
        result = parser._parse_markdown_bytes(b"# H1\n## H2\n### H3\ntext")
        assert result == "H1\nH2\nH3\ntext"

    def test_parse_md_strips_images(self):
        parser = DocumentParser()
        result = parser._parse_markdown_bytes(
            b"text ![alt](img.png) more text"
        )
        assert "img.png" not in result
        assert "more text" in result
