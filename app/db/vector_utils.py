"""Helpers for pgvector literals."""
from __future__ import annotations

from app.services.embedding_service import EMBEDDING_DIMENSION


def vector_literal(values: list[float]) -> str:
    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f'expected embedding dimension {EMBEDDING_DIMENSION}, got {len(values)}'
        )
    return '[' + ','.join(f'{value:.8f}' for value in values) + ']'
