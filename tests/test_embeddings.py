"""Embedding tests — offline (HashFallbackProvider) by default."""

from doc_pipeline.embeddings import EmbeddingGenerator, MockEmbeddingGenerator


class TestEmbeddingGenerator:
    def test_offline_is_deterministic(self):
        gen = EmbeddingGenerator(offline=True)
        v1 = gen.embed_text("hello world")
        v2 = gen.embed_text("hello world")
        assert v1 == v2
        assert all(isinstance(x, float) for x in v1)

    def test_different_text_different_vectors(self):
        gen = EmbeddingGenerator(offline=True)
        assert gen.embed_text("alpha") != gen.embed_text("beta")

    def test_no_api_key_falls_back_to_offline(self):
        gen = EmbeddingGenerator(api_key=None)
        assert gen.offline is True
        assert len(gen.embed_text("text")) == gen.dimensions

    def test_embed_chunks_attaches_vectors(self, sample_chunks):
        gen = EmbeddingGenerator(offline=True)
        result = gen.embed_chunks(sample_chunks)
        assert len(result) == 2
        assert all(len(c["embedding"]) > 0 for c in result)

    def test_dimensions_property(self):
        gen = EmbeddingGenerator(offline=True)
        assert gen.dimensions == len(gen.embed_text("anything"))


class TestMockEmbeddingGenerator:
    def test_requested_dimension_respected(self):
        gen = MockEmbeddingGenerator(dimension=128)
        assert len(gen.embed_text("hello")) == 128

    def test_default_dimension(self):
        gen = MockEmbeddingGenerator()
        assert len(gen.embed_text("test")) == 1536

    def test_deterministic(self):
        gen = MockEmbeddingGenerator(dimension=64)
        assert gen.embed_text("same") == gen.embed_text("same")
