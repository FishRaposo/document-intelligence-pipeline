"""Chunking tests for both the shared-backed ``Chunker`` and the legacy
``SlidingWindowChunker`` word-window chunker."""

import pytest
from shared_core.docparse import ChunkStrategy

from doc_pipeline.chunkers import Chunker, ChunkError, SlidingWindowChunker


class TestChunker:
    def test_semantic_chunks_have_shape(self):
        chunker = Chunker(strategy=ChunkStrategy.SEMANTIC, chunk_size=80)
        text = "Sentence one is here. Sentence two follows. " * 8
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert all({"chunk_id", "content", "word_count"} <= set(c) for c in chunks)
        ids = [c["chunk_id"] for c in chunks]
        assert ids == list(range(len(ids)))

    def test_fixed_strategy_respects_size(self):
        chunker = Chunker(strategy=ChunkStrategy.FIXED, chunk_size=50, overlap=10)
        text = "x" * 200
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1
        assert all(len(c["content"]) <= 50 for c in chunks)

    def test_empty_text_returns_no_chunks(self):
        chunker = Chunker()
        assert chunker.chunk_text("") == []

    def test_invalid_overlap_raises(self):
        with pytest.raises(ChunkError, match="overlap"):
            Chunker(chunk_size=10, overlap=10)

    def test_word_count_populated(self):
        chunker = Chunker(strategy=ChunkStrategy.SEMANTIC, chunk_size=200)
        chunks = chunker.chunk_text("alpha beta gamma delta epsilon.")
        assert chunks[0]["word_count"] == 5


class TestSlidingWindowChunker:
    def test_basic(self):
        chunker = SlidingWindowChunker(chunk_size=4, overlap=1)
        chunks = chunker.chunk_text("one two three four five six seven")
        assert len(chunks) >= 1
        assert all("content" in c for c in chunks)

    def test_overlap_validation(self):
        with pytest.raises(ChunkError, match="overlap"):
            SlidingWindowChunker(chunk_size=5, overlap=5)

    def test_shorter_than_chunk_size(self):
        chunker = SlidingWindowChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk_text("short text")
        assert len(chunks) == 1
        assert chunks[0]["content"] == "short text"

    def test_no_overlap(self):
        chunker = SlidingWindowChunker(chunk_size=2, overlap=0)
        chunks = chunker.chunk_text("a b c d e f")
        assert [c["content"] for c in chunks] == ["a b", "c d", "e f"]

    def test_empty(self):
        chunker = SlidingWindowChunker(chunk_size=5, overlap=1)
        assert chunker.chunk_text("") == []

    def test_sequential_ids(self):
        chunker = SlidingWindowChunker(chunk_size=2, overlap=0)
        chunks = chunker.chunk_text("a b c d e f g h")
        assert [c["chunk_id"] for c in chunks] == list(range(len(chunks)))
