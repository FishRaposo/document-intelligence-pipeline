"""Document parsing built on ``shared_core.docparse``.

This module is a thin adapter over the shared parsing layer: ``get_parser``
resolves a concrete parser by extension/MIME, and each parser returns a uniform
``ParsedDocument`` (text + title + metadata + page_count). PDF/DOCX/HTML parsers
dynamically import their heavy dependencies (PyMuPDF, python-docx, beautifulsoup4)
and raise a friendly ``ImportError`` when missing — we translate those into a
project-level :class:`ParseError` so callers get one stable error type to quarantine.

Plain text and Markdown work with no optional dependencies at all.
"""

import os
from typing import Optional

from shared_core.docparse import ParsedDocument, get_parser
from shared_core.errors import ValidationError

# Extensions we route through shared_core.docparse.
SUPPORTED_EXTENSIONS = (".txt", ".md", ".markdown", ".html", ".htm", ".pdf", ".docx")

# Extensions that require an optional heavy dependency to be installed.
OPTIONAL_DEP_EXTENSIONS = (".pdf", ".docx", ".html", ".htm")


class ParseError(Exception):
    """Raised when a document cannot be parsed.

    Wraps the underlying cause (unsupported format, missing optional dependency,
    corrupt bytes) so the ingestion pipeline can record a single quarantine reason.
    """

    def __init__(self, message: str, filename: Optional[str] = None):
        self.filename = filename
        super().__init__(message)


class DocumentParser:
    """Resolves and runs the appropriate ``shared_core.docparse`` parser."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        """Parse raw bytes into a :class:`ParsedDocument`.

        Raises :class:`ParseError` for unsupported formats, missing optional
        dependencies, or any decode/parse failure.
        """
        ext = os.path.splitext(filename)[1].lower()
        try:
            parser = get_parser(filename)
        except ValidationError as exc:
            raise ParseError(
                f"Unsupported format: {ext or filename}", filename=filename
            ) from exc

        try:
            return parser.parse(content, filename=filename)
        except ImportError as exc:
            # Optional dependency (pymupdf / python-docx / beautifulsoup4) missing.
            raise ParseError(str(exc), filename=filename) from exc
        except ParseError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalise to one quarantine reason
            raise ParseError(
                f"Failed to parse '{filename}': {exc}", filename=filename
            ) from exc

    def parse_bytes(self, content: bytes, filename: str) -> str:
        """Backwards-compatible helper returning only the extracted text."""
        return self.parse(content, filename).text

    def parse_file(self, filepath: str) -> str:
        """Read a file from disk and return its extracted text."""
        with open(filepath, "rb") as handle:
            content = handle.read()
        return self.parse_bytes(content, os.path.basename(filepath))

    @staticmethod
    def file_format(filename: str) -> str:
        """Return the lowercased extension (without the dot) for a filename."""
        ext = os.path.splitext(filename)[1].lower()
        return ext[1:] if ext.startswith(".") else ext
