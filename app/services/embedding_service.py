"""OpenAI embedding service for RAG indexing."""
from __future__ import annotations

from typing import Any, Callable, Mapping

from app.config import Config

EMBEDDING_DIMENSION = 1536
DEFAULT_BATCH_SIZE = 64


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""


class EmbeddingService:
    """Generate embeddings via OpenAI or an injectable embedder."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        embedder: Callable[[list[str], str | None], list[list[float]]] | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        self._config = dict(config) if config is not None else None
        self._embedder = embedder
        self._batch_size = max(1, int(batch_size))

    def _resolve_config(self) -> dict[str, Any]:
        if self._config is not None:
            return self._config
        try:
            from flask import current_app

            return dict(current_app.config)
        except RuntimeError:
            return {
                'OPENAI_API_KEY': Config.OPENAI_API_KEY,
                'EMBEDDING_MODEL': Config.EMBEDDING_MODEL,
            }

    def embed_texts(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        if not texts:
            return []

        cfg = self._resolve_config()
        model_name = model or str(cfg.get('EMBEDDING_MODEL') or Config.EMBEDDING_MODEL)

        if self._embedder is not None:
            vectors = self._embedder(texts, model_name)
        else:
            vectors = self._embed_with_openai(texts, model_name, cfg)

        self._validate_vectors(vectors, expected=len(texts))
        return vectors

    def _embed_with_openai(
        self,
        texts: list[str],
        model_name: str,
        cfg: Mapping[str, Any],
    ) -> list[list[float]]:
        api_key = str(cfg.get('OPENAI_API_KEY') or '').strip()
        if not api_key:
            raise EmbeddingError('OPENAI_API_KEY is not configured')

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise EmbeddingError('openai package is not installed') from exc

        client = OpenAI(api_key=api_key)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start:start + self._batch_size]
            try:
                response = client.embeddings.create(model=model_name, input=batch)
            except Exception as exc:
                raise EmbeddingError(str(exc)) from exc
            vectors.extend(item.embedding for item in response.data)
        return vectors

    @staticmethod
    def _validate_vectors(vectors: list[list[float]], *, expected: int) -> None:
        if len(vectors) != expected:
            raise EmbeddingError(
                f'expected {expected} embeddings, got {len(vectors)}'
            )
        for index, vector in enumerate(vectors):
            if len(vector) != EMBEDDING_DIMENSION:
                raise EmbeddingError(
                    f'embedding {index} has dimension {len(vector)}, expected {EMBEDDING_DIMENSION}'
                )
