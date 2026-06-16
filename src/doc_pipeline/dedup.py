"""Content-hash deduplication helpers built on ``shared_core.docparse``.

Document-level dedup uses ``compute_hash`` over the cleaned text so re-ingesting
an identical file is a no-op. Chunk-level dedup uses ``filter_duplicates`` to drop
repeated chunks (common with overlapping windows over boilerplate) before they are
embedded and stored.
"""

from typing import Any, Dict, List

from shared_core.docparse import compute_hash, filter_duplicates


def content_hash(content: str) -> str:
    """Return the SHA-256 hex digest of ``content``."""
    return compute_hash(content)


def dedup_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove chunks with duplicate content, preserving first-seen order.

    ``chunk_id`` values are re-numbered sequentially after filtering so downstream
    consumers see a contiguous index.
    """
    unique = filter_duplicates(chunks, key=lambda c: compute_hash(c.get("content", "")))
    for idx, chunk in enumerate(unique):
        chunk["chunk_id"] = idx
    return unique
