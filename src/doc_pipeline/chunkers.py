from typing import Any, Dict, List


class ChunkError(Exception):
    """Raised when chunking fails."""


class SlidingWindowChunker:
    """Splits a document text block into overlapping chunks."""

    def __init__(self, chunk_size: int = 200, overlap: int = 50):
        if overlap >= chunk_size:
            raise ChunkError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        words = text.split()
        chunks = []
        step = self.chunk_size - self.overlap
        idx = 0
        chunk_id = 0

        while idx < len(words):
            chunk_words = words[idx : idx + self.chunk_size]
            if len(chunk_words) < self.chunk_size and chunks:
                break
            chunk_content = " ".join(chunk_words)
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "content": chunk_content,
                    "word_count": len(chunk_words),
                }
            )
            idx += step
            chunk_id += 1

        return chunks
