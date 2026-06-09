import os
from typing import Optional

from loguru import logger


class ParseError(Exception):
    """Raised when a document cannot be parsed."""

    def __init__(self, message: str, filename: Optional[str] = None):
        self.filename = filename
        super().__init__(message)


class ChunkError(Exception):
    """Raised when chunking fails."""

    pass


class DocumentParser:
    """Reads various file formats and extracts clean text."""

    def parse_bytes(self, content: bytes, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".txt":
            return content.decode("utf-8")
        elif ext == ".md":
            return self._parse_markdown_bytes(content)
        elif ext == ".html" or ext == ".htm":
            return self._parse_html_bytes(content)
        elif ext == ".pdf":
            return self._parse_pdf_bytes(content)
        elif ext == ".docx":
            return self._parse_docx_bytes(content)
        else:
            raise ParseError(f"Unsupported format: {ext}", filename=filename)

    def parse_file(self, filepath: str) -> str:
        with open(filepath, "rb") as f:
            content = f.read()
        return self.parse_bytes(content, os.path.basename(filepath))

    def _parse_markdown_bytes(self, content: bytes) -> str:
        import re

        text = content.decode("utf-8")
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
        return text.strip()

    def _parse_html_bytes(self, content: bytes) -> str:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except ImportError:
            logger.warning("beautifulsoup4 not installed — using naive HTML parsing")
            text = content.decode("utf-8")
            text = text.replace("<html>", "").replace("</html>", "")
            text = text.replace("<body>", "").replace("</body>", "")
            return text.strip()

    def _parse_pdf_bytes(self, content: bytes) -> str:
        try:
            import io

            import pdfplumber

            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except ImportError as e:
            raise ParseError(
                "pdfplumber not installed. Install via 'pip install pdfplumber'"
            ) from e

    def _parse_docx_bytes(self, content: bytes) -> str:
        try:
            import io

            import docx

            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError as e:
            raise ParseError(
                "python-docx not installed. Install via 'pip install python-docx'"
            ) from e
