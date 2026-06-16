"""Text chunking built on ``shared_core.docparse.chunk_text``.

The shared layer provides three strategies (FIXED character windows, SEMANTIC
sentence packing, STRUCTURAL heading splits). This module exposes a small
``Chunker`` adapter that returns chunk dicts (``chunk_id`` / ``content`` /
``word_count``) — the shape the rest of the pipeline, the API, and the JSONL
exporter expect. ``SlidingWindowChunker`` is retained as a word-window chunker
for backwards compatibility and the demo.
"""

from typing import Any, Dict, List

from shared_core.docparse import ChunkStrategy, chunk_text


class ChunkError(Exception):
    """Raised when chunking is misconfigured."""


def _to_records(pieces: List[str]) -> List[Dict[str, Any]]:
    """Wrap raw chunk strings into the pipeline's chunk-record shape."""
    return [
        {
            "chunk_id": idx,
            "content": piece,
            "word_count": len(piece.split()),
        }
        for idx, piece in enumerate(pieces)
    ]


class Chunker:
    """Adapter over ``shared_core.docparse.chunk_text`` returning chunk records."""

    def __init__(
        self,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        chunk_size: int = 512,
        overlap: int = 64,
    ):
        if overlap >= chunk_size:
            raise ChunkError("overlap must be less than chunk_size")
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        pieces = chunk_text(
            text,
            strategy=self.strategy,
            chunk_size=self.chunk_size,
            overlap=self.overlap,
        )
        return _to_records(pieces)


class SlidingWindowChunker:
    """Word-window chunker with overlap (kept for the demo and prior tests).

    Splits on whitespace and emits overlapping windows of ``chunk_size`` words.
    The final short window is dropped once at least one full chunk exists so we
    do not emit a tiny tail chunk — matching the original pipeline behaviour.
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 50):
        if overlap >= chunk_size:
            raise ChunkError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        words = text.split()
        chunks: List[Dict[str, Any]] = []
        step = self.chunk_size - self.overlap
        idx = 0
        chunk_id = 0

        while idx < len(words):
            chunk_words = words[idx : idx + self.chunk_size]
            if len(chunk_words) < self.chunk_size and chunks:
                break
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "content": " ".join(chunk_words),
                    "word_count": len(chunk_words),
                }
            )
            idx += step
            chunk_id += 1

        return chunks
