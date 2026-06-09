from typing import Any, Dict, List

from loguru import logger


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class MockEmbeddingGenerator:
    """Generates mock vector dimensions representing semantic space."""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def embed_text(self, text: str) -> List[float]:
        val = sum(ord(c) for c in text[:100]) / 1000.0
        return [val * (i + 1) / self.dimension for i in range(self.dimension)]

    def embed_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for chunk in chunks:
            chunk["embedding"] = self.embed_text(chunk["content"])
        return chunks


class OpenAIEmbeddingGenerator:
    """Generates embeddings using OpenAI API."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "text-embedding-3-small",
    ):
        self.api_key = api_key
        self.model = model

    def embed_text(self, text: str) -> List[float]:
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            response = client.embeddings.create(
                model=self.model, input=text
            )
            return response.data[0].embedding
        except ImportError as e:
            raise EmbeddingError(
                "openai not installed. Install via 'pip install openai'"
            ) from e

    def embed_chunks(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        for chunk in chunks:
            try:
                chunk["embedding"] = self.embed_text(chunk["content"])
            except Exception as e:
                logger.warning(
                    "Embedding failed for chunk {}: {}",
                    chunk.get("chunk_id"),
                    e,
                )
                chunk["embedding"] = []
        return chunks
