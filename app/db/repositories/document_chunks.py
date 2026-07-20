"""PostgreSQL repository for indexed document chunks."""
from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from psycopg2.extras import execute_values

from app.db.connection import get_postgres_connection
from app.services.chunking import ChunkDraft
from app.services.embedding_service import EMBEDDING_DIMENSION


def _vector_literal(values: list[float]) -> str:
    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f'expected embedding dimension {EMBEDDING_DIMENSION}, got {len(values)}'
        )
    return '[' + ','.join(f'{value:.8f}' for value in values) + ']'


def delete_by_doc_id(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> int:
    """Delete all chunks for a document. Returns number of rows removed."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'DELETE FROM document_chunks WHERE doc_id = %s',
                (str(doc_id),),
            )
            deleted = cursor.rowcount
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def count_by_doc_id(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> int:
    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM document_chunks WHERE doc_id = %s',
                (str(doc_id),),
            )
            row = cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def insert_batch(
    *,
    doc_id: str | uuid.UUID,
    entity_id: str | uuid.UUID,
    category: str | None,
    chunks: list[ChunkDraft],
    embeddings: list[list[float]],
    metadata_base: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> int:
    """Insert chunk rows with pgvector embeddings. Returns inserted count."""
    if len(chunks) != len(embeddings):
        raise ValueError('chunks and embeddings length mismatch')
    if not chunks:
        return 0

    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        metadata = dict(metadata_base)
        metadata.setdefault('chunk_index', chunk.chunk_index)
        rows.append((
            str(doc_id),
            str(entity_id),
            chunk.chunk_index,
            chunk.page,
            chunk.content,
            category,
            _vector_literal(embedding),
            json.dumps(metadata),
        ))

    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO document_chunks (
                    doc_id,
                    entity_id,
                    chunk_index,
                    page,
                    content,
                    category,
                    embedding,
                    metadata
                ) VALUES %s
                """,
                rows,
                template='(%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb)',
            )
        conn.commit()
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
