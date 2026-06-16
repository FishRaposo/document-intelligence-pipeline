"""Metadata extraction for parsed documents.

Combines parser-provided metadata (PDF/DOCX core properties, HTML ``<title>``)
with cheap heuristics over the extracted text: a title (first heading / first
non-empty line), an author (``By: ...`` / ``Author: ...`` patterns), any ISO-ish
dates found in the body, and a word/character count. Everything here is pure and
dependency-free so it runs offline.
"""

import re
from typing import Any, Dict, Optional

from shared_core.docparse import ParsedDocument

# 2024-01-31, 2024/01/31, 31 Jan 2024, January 31, 2024
_DATE_RE = re.compile(
    r"\b("
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"
    r"|(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+\d{4}"
    r")\b"
)
_AUTHOR_RE = re.compile(
    r"^\s*(?:by|author|written by)\s*[:\-]?\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


def _derive_title(parsed: ParsedDocument, text: str, filename: str) -> str:
    """Pick the most specific available title."""
    if parsed.title:
        return parsed.title.strip()
    heading = _HEADING_RE.search(text)
    if heading:
        return heading.group(1).strip()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return filename


def _derive_author(parsed: ParsedDocument, text: str) -> Optional[str]:
    """Pull an author from parser metadata or a ``By:``-style line."""
    meta_author = parsed.metadata.get("author") or parsed.metadata.get("Author")
    if meta_author:
        return str(meta_author).strip()
    match = _AUTHOR_RE.search(text)
    if match:
        candidate = match.group(1).strip()
        # Avoid swallowing whole sentences.
        if candidate and len(candidate) <= 120:
            return candidate
    return None


def extract_metadata(
    parsed: ParsedDocument, filename: str, file_size: int = 0
) -> Dict[str, Any]:
    """Return a metadata dict for a parsed document.

    Keys: ``title``, ``author`` (optional), ``dates`` (list, de-duplicated in
    order), ``word_count``, ``char_count``, ``page_count``, ``file_size_bytes``,
    plus any keys the parser itself emitted under ``source_metadata``.
    """
    text = parsed.text or ""
    seen: set[str] = set()
    dates = []
    for match in _DATE_RE.findall(text):
        if match not in seen:
            seen.add(match)
            dates.append(match)

    return {
        "title": _derive_title(parsed, text, filename),
        "author": _derive_author(parsed, text),
        "dates": dates,
        "word_count": len(text.split()),
        "char_count": len(text),
        "page_count": parsed.page_count,
        "file_size_bytes": file_size,
        "source_metadata": dict(parsed.metadata),
    }
