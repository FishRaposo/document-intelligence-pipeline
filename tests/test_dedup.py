"""Content-hash deduplication tests."""

from doc_pipeline.dedup import content_hash, dedup_chunks


class TestDedup:
    def test_content_hash_stable(self):
        assert content_hash("hello") == content_hash("hello")
        assert content_hash("hello") != content_hash("world")
        assert len(content_hash("x")) == 64

    def test_dedup_chunks_removes_duplicates(self):
        chunks = [
            {"chunk_id": 0, "content": "alpha", "word_count": 1},
            {"chunk_id": 1, "content": "beta", "word_count": 1},
            {"chunk_id": 2, "content": "alpha", "word_count": 1},
        ]
        result = dedup_chunks(chunks)
        assert [c["content"] for c in result] == ["alpha", "beta"]

    def test_dedup_renumbers_ids(self):
        chunks = [
            {"chunk_id": 5, "content": "a", "word_count": 1},
            {"chunk_id": 9, "content": "a", "word_count": 1},
            {"chunk_id": 12, "content": "b", "word_count": 1},
        ]
        result = dedup_chunks(chunks)
        assert [c["chunk_id"] for c in result] == [0, 1]

    def test_dedup_preserves_order(self):
        chunks = [
            {"chunk_id": i, "content": c, "word_count": 1}
            for i, c in enumerate("abcba")
        ]
        result = dedup_chunks(chunks)
        assert [c["content"] for c in result] == ["a", "b", "c"]
