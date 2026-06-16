"""Embedding generation built on ``shared_core.embeddings``.

Offline-first: with no API key (or ``offline=True``) we use the deterministic
``HashFallbackProvider`` so demos and tests embed with no network. When an
OpenAI key is present, ``get_embedding_provider`` returns the real
``OpenAIEmbeddingProvider``. The shared providers are async, so this adapter
exposes a synchronous facade (``embed_text`` / ``embed_chunks``) that the
pipeline, worker, and exporter consume without caring which backend is live.
"""

import asyncio
from typing import Any, Coroutine, Dict, List, Optional, TypeVar

from loguru import logger
from shared_core.embeddings import EmbeddingProvider, get_embedding_provider

_T = TypeVar("_T")


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


def _run_sync(coro: Coroutine[Any, Any, _T]) -> _T:
    """Run an async coroutine to completion from synchronous code.

    Uses ``asyncio.run`` when no loop is active. If a loop is already running in
    this thread (e.g. inside an async framework), the coroutine is executed on a
    short-lived worker thread so we never leak an un-awaited coroutine.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(coro)).result()


class EmbeddingGenerator:
    """Synchronous facade over a ``shared_core`` async embedding provider.

    Parameters
    ----------
    api_key:
        OpenAI key. When falsy (the default) the offline hash fallback is used.
    model:
        Embedding model name (only used for the OpenAI path).
    offline:
        Force the deterministic offline provider even when a key is present.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        offline: bool = False,
        provider: Optional[EmbeddingProvider] = None,
    ):
        self.model = model
        self.offline = offline or not api_key
        self._provider = provider or get_embedding_provider(
            api_key=api_key, model=model, offline=self.offline
        )

    @property
    def dimensions(self) -> int:
        """Best-effort dimensionality of the active provider (offline default)."""
        return int(getattr(self._provider, "dimensions", 384) or 384)

    def embed_text(self, text: str) -> List[float]:
        """Return the embedding vector for a single string."""
        try:
            result = _run_sync(self._provider.embed(text))
            return list(result.vector)
        except ImportError as exc:  # openai requested but not installed
            raise EmbeddingError(str(exc)) from exc

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach an ``embedding`` field to each chunk record in place."""
        for chunk in chunks:
            try:
                chunk["embedding"] = self.embed_text(chunk.get("content", ""))
            except Exception as exc:  # noqa: BLE001 - degrade gracefully per chunk
                logger.warning(
                    "Embedding failed for chunk {}: {}",
                    chunk.get("chunk_id"),
                    exc,
                )
                chunk["embedding"] = []
        return chunks


# Backwards-compatible alias: the previous mock generator is now the offline
# deterministic provider exposed through the same interface.
class MockEmbeddingGenerator(EmbeddingGenerator):
    """Deterministic offline embedding generator (``HashFallbackProvider``).

    ``dimension`` is accepted for API compatibility with the prior mock; the
    underlying offline provider emits 384-dim vectors. When a specific dimension
    is requested we resize deterministically so existing tests still pass.
    """

    def __init__(self, dimension: int = 1536):
        super().__init__(offline=True)
        self._requested_dim = dimension

    def embed_text(self, text: str) -> List[float]:
        vector = super().embed_text(text)
        target = self._requested_dim
        if len(vector) == target:
            return vector
        if len(vector) > target:
            return vector[:target]
        # Tile the deterministic vector up to the requested dimensionality.
        out: List[float] = []
        while len(out) < target:
            out.extend(vector)
        return out[:target]
