import pytest
from doc_pipeline.chunkers import ChunkError, SlidingWindowChunker


class TestSlidingWindowChunker:
    def test_chunks_text_basic(self):
        chunker = SlidingWindowChunker(chunk_size=4, overlap=1)
        text = "one two three four five six seven"
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert all("content" in c for c in chunks)
        assert all("chunk_id" in c for c in chunks)
        assert all("word_count" in c for c in chunks)

    def test_overlap_must_be_less_than_chunk_size(self):
        with pytest.raises(ChunkError, match="overlap"):
            SlidingWindowChunker(chunk_size=5, overlap=5)

    def test_text_shorter_than_chunk_size(self):
        chunker = SlidingWindowChunker(chunk_size=100, overlap=10)
        text = "short text"
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["content"] == "short text"

    def test_text_exact_chunk_size(self):
        chunker = SlidingWindowChunker(chunk_size=3, overlap=0)
        text = "one two three"
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["word_count"] == 3

    def test_no_overlap_chunks(self):
        chunker = SlidingWindowChunker(chunk_size=2, overlap=0)
        text = "a b c d e f"
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 3
        assert chunks[0]["content"] == "a b"
        assert chunks[1]["content"] == "c d"
        assert chunks[2]["content"] == "e f"

    def test_with_overlap(self):
        chunker = SlidingWindowChunker(chunk_size=3, overlap=1)
        text = "a b c d e f"
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2
        assert "c" in chunks[0]["content"]
        assert "c" in chunks[1]["content"]

    def test_empty_text(self):
        chunker = SlidingWindowChunker(chunk_size=5, overlap=1)
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_ids_sequential(self):
        chunker = SlidingWindowChunker(chunk_size=2, overlap=0)
        text = "a b c d e f g h"
        chunks = chunker.chunk_text(text)
        ids = [c["chunk_id"] for c in chunks]
        assert ids == list(range(len(ids)))

    def test_last_chunk_not_too_small(self):
        chunker = SlidingWindowChunker(chunk_size=4, overlap=1)
        text = "a b c d e f g"
        chunks = chunker.chunk_text(text)
        assert len(chunks) <= 3
