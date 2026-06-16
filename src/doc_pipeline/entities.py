"""Lightweight, dependency-free entity extraction.

A heuristic alternative to a full NER model (spaCy) so the pipeline runs offline
with zero heavy dependencies. Extracts:

- ``emails``  — RFC-ish email addresses
- ``urls``    — http/https URLs
- ``phones``  — common phone-number shapes
- ``capitalised`` — capitalised n-grams (1-3 tokens) as a proper-noun proxy

Each list is de-duplicated while preserving first-seen order.
"""

import re
from typing import Dict, List

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_URL_RE = re.compile(r"https?://[^\s<>\"')]+")
# Trailing punctuation that should not be part of a captured URL.
_URL_TRAILING = ".,;:!?)]}>'\""
_PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[\s.\-]?)?(?:\(\d{2,4}\)[\s.\-]?)?\d{3,4}[\s.\-]\d{3,4}\b"
)
# One to three consecutive Capitalised words (proper-noun proxy).
_CAP_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")

# Common sentence-initial words we do not want flagged as entities.
_STOPWORDS = {
    "The",
    "This",
    "That",
    "These",
    "Those",
    "It",
    "A",
    "An",
    "In",
    "On",
    "At",
    "For",
    "And",
    "But",
    "Or",
    "If",
    "When",
    "While",
    "However",
    "Modern",
    "Every",
    "By",
    "Author",
    "Contact",
    "Published",
    "Dr",
    "Mr",
    "Mrs",
    "Ms",
}


def _dedup(values: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract emails, urls, phone numbers, and capitalised n-grams from ``text``."""
    if not text:
        return {"emails": [], "urls": [], "phones": [], "capitalised": []}

    urls = _dedup(u.rstrip(_URL_TRAILING) for u in _URL_RE.findall(text))
    # Strip URLs/emails before phone + capitalised passes to reduce false hits.
    scrubbed = _URL_RE.sub(" ", text)
    emails = _dedup(_EMAIL_RE.findall(scrubbed))
    scrubbed = _EMAIL_RE.sub(" ", scrubbed)

    phones = _dedup(p.strip() for p in _PHONE_RE.findall(scrubbed))

    capitalised = [
        phrase
        for phrase in _CAP_RE.findall(scrubbed)
        if phrase not in _STOPWORDS and phrase.split()[0] not in _STOPWORDS
    ]

    return {
        "emails": emails,
        "urls": urls,
        "phones": phones,
        "capitalised": _dedup(capitalised),
    }
