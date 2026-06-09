import pytest
from doc_pipeline.embeddings import (
    EmbeddingError,
    MockEmbeddingGenerator,
    OpenAIEmbeddingGenerator,
)


class TestMockEmbeddingGenerator:
    def test_embed_text_returns_correct_dimension(self):
        gen = MockEmbeddingGenerator(dimension=10)
        result = gen.embed_text("hello")
        assert len(result) == 10
        assert all(isinstance(v, float) for v in result)

    def test_embed_text_different_inputs_different_vectors(self):
        gen = MockEmbeddingGenerator(dimension=10)
        v1 = gen.embed_text("hello")
        v2 = gen.embed_text("goodbye")
        assert v1 != v2

    def test_embed_chunks_adds_embedding_field(self, sample_chunks):
        gen = MockEmbeddingGenerator(dimension=10)
        result = gen.embed_chunks(sample_chunks)
        assert len(result) == 2
        assert len(result[0]["embedding"]) == 10
        assert len(result[1]["embedding"]) == 10

    def test_default_dimension(self):
        gen = MockEmbeddingGenerator()
        result = gen.embed_text("test")
        assert len(result) == 1536


class TestOpenAIEmbeddingGenerator:
    def test_init_with_api_key(self):
        gen = OpenAIEmbeddingGenerator(api_key="sk-test")
        assert gen.api_key == "sk-test"
        assert gen.model == "text-embedding-3-small"

    def test_embed_text_requires_openai(self, monkeypatch):
        gen = OpenAIEmbeddingGenerator(api_key="sk-test")
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("No openai")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(EmbeddingError, match="openai"):
            gen.embed_text("test")

    def test_embed_chunks_handles_failure_gracefully(self, sample_chunks):
        gen = OpenAIEmbeddingGenerator(api_key="sk-test")

        def failing_embed(text):
            raise Exception("API error")

        gen.embed_text = failing_embed
        result = gen.embed_chunks(sample_chunks)
        assert len(result) == 2
        assert result[0]["embedding"] == []
