"""PostgreSQL repository for guide documents (admin CRUD)."""
from __future__ import annotations

import json
import uuid
from typing import Any, Callable, Mapping

from psycopg2.extras import RealDictCursor

from app.db.connection import get_postgres_connection
from app.db.mappers import document_row_to_json
from app.db.vector_utils import vector_literal
from app.services.embedding_service import EmbeddingError, EmbeddingService


class DocumentValidationError(ValueError):
    """Invalid document field values before hitting the database."""


class SearchValidationError(ValueError):
    """Invalid semantic search parameters."""


class EntityNotFoundError(LookupError):
    """Entity missing or inactive for document search."""


def _validate_title(title: str) -> str:
    value = str(title or '').strip()
    if not value:
        raise DocumentValidationError('title is required')
    return value


def _validate_source_filename(source_filename: str) -> str:
    value = str(source_filename or '').strip()
    if not value:
        raise DocumentValidationError('source_filename is required')
    return value


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _row_to_document(row: dict | None) -> dict | None:
    if row is None:
        return None
    return document_row_to_json(dict(row))


def _truncate_summary(text: str, max_len: int = 200) -> str:
    value = str(text or '').strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 3].rstrip() + '...'


def _chunk_hit_to_result(row: Mapping[str, Any]) -> dict:
    content = str(row.get('content') or '')
    metadata = row.get('metadata') or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    elif not isinstance(metadata, dict):
        metadata = {}

    doc_title = str(row.get('doc_title') or '')
    source_filename = str(row.get('source_filename') or '')
    chunk_index = metadata.get('chunk_index', row.get('chunk_index'))

    return {
        'source': doc_title,
        'page': row.get('page'),
        'summary': _truncate_summary(content),
        'content': content,
        'doc_id': str(row.get('doc_id')),
        'entity_id': str(row.get('entity_id')),
        'metadata': {
            'doc_title': doc_title,
            'source_file': source_filename,
            'chunk_index': chunk_index,
        },
    }


def _ensure_active_entity(entity_id: str | uuid.UUID, *, config: Mapping[str, Any] | None) -> None:
    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM entities
                WHERE entity_id = %s AND is_active = true
                """,
                (str(entity_id),),
            )
            found = cursor.fetchone() is not None
    finally:
        conn.close()
    if not found:
        raise EntityNotFoundError(f'entity not found or inactive: {entity_id}')


def search(
    *,
    query: str,
    entity_id: str | uuid.UUID,
    limit: int = 5,
    category: str | None = None,
    doc_id: str | uuid.UUID | None = None,
    embedder: Callable[[list[str], str | None], list[list[float]]] | None = None,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """Semantic search over indexed document chunks for an active entity."""
    normalized_query = str(query or '').strip()
    if not normalized_query:
        raise SearchValidationError('query is required')
    if not str(entity_id or '').strip():
        raise SearchValidationError('entity_id is required')

    try:
        resolved_limit = int(limit)
    except (TypeError, ValueError):
        resolved_limit = 5
    resolved_limit = max(1, min(resolved_limit, 20))

    normalized_category = _normalize_optional_text(category)
    normalized_doc_id = str(doc_id) if doc_id is not None else None

    _ensure_active_entity(entity_id, config=config)

    try:
        query_vector = EmbeddingService(config=config, embedder=embedder).embed_texts(
            [normalized_query]
        )[0]
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(str(exc)) from exc

    vector_param = vector_literal(query_vector)
    entity_param = str(entity_id)

    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    dc.chunk_id,
                    dc.doc_id,
                    dc.entity_id,
                    dc.chunk_index,
                    dc.page,
                    dc.content,
                    dc.metadata,
                    gd.title AS doc_title,
                    gd.source_filename,
                    dc.embedding <=> %s::vector AS distance
                FROM document_chunks dc
                INNER JOIN guide_documents gd ON gd.doc_id = dc.doc_id
                INNER JOIN entities e ON e.entity_id = dc.entity_id AND e.is_active = true
                WHERE dc.entity_id = %s
                  AND gd.status = 'indexed'
                  AND (%s IS NULL OR dc.doc_id = %s::uuid)
                  AND (%s IS NULL OR dc.category = %s)
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    vector_param,
                    entity_param,
                    normalized_doc_id,
                    normalized_doc_id,
                    normalized_category,
                    normalized_category,
                    vector_param,
                    resolved_limit,
                ),
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    results = [_chunk_hit_to_result(dict(row)) for row in rows]
    return {
        'query': normalized_query,
        'entity_id': entity_param,
        'total': len(results),
        'results': results,
    }


def create(
    *,
    doc_id: str | uuid.UUID,
    entity_id: str | uuid.UUID,
    title: str,
    source_filename: str,
    storage_path: str,
    category: str | None = None,
    mime_type: str = 'application/pdf',
    config: Mapping[str, Any] | None = None,
) -> dict:
    """Insert a guide document row and return admin JSON."""
    validated_title = _validate_title(title)
    validated_filename = _validate_source_filename(source_filename)
    normalized_category = _normalize_optional_text(category)
    normalized_storage_path = str(storage_path or '').strip()
    if not normalized_storage_path:
        raise DocumentValidationError('storage_path is required')

    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO guide_documents (
                    doc_id,
                    entity_id,
                    title,
                    category,
                    source_filename,
                    storage_path,
                    mime_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    str(doc_id),
                    str(entity_id),
                    validated_title,
                    normalized_category,
                    validated_filename,
                    normalized_storage_path,
                    mime_type,
                ),
            )
            row = cursor.fetchone()
        conn.commit()
        return _row_to_document(row)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_all(
    *,
    entity_id: str | uuid.UUID | None = None,
    config: Mapping[str, Any] | None = None,
) -> list[dict]:
    """Return documents ordered by newest first, optionally filtered by entity."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if entity_id is not None:
                cursor.execute(
                    """
                    SELECT *
                    FROM guide_documents
                    WHERE entity_id = %s
                    ORDER BY created_at DESC
                    """,
                    (str(entity_id),),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM guide_documents
                    ORDER BY created_at DESC
                    """
                )
            rows = cursor.fetchall()
        return [_row_to_document(dict(row)) for row in rows]
    finally:
        conn.close()


def get_by_id(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> dict | None:
    """Return one document by UUID or None if missing."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT * FROM guide_documents WHERE doc_id = %s',
                (str(doc_id),),
            )
            row = cursor.fetchone()
        return _row_to_document(dict(row) if row else None)
    finally:
        conn.close()


def get_raw_by_id(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> dict | None:
    """Return raw guide_documents row for internal pipeline use."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT * FROM guide_documents WHERE doc_id = %s',
                (str(doc_id),),
            )
            row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_indexing_state(
    doc_id: str | uuid.UUID,
    status: str,
    *,
    error_message: str | None = None,
    pages_count: int | None = None,
    chunks_count: int | None = None,
    embedded_chunks_count: int | None = None,
    embedding_model: str | None = None,
    indexed_at: Any = None,
    clear_error: bool = False,
    config: Mapping[str, Any] | None = None,
) -> dict | None:
    """Update pipeline status and counters for a document."""
    updates: dict[str, Any] = {'status': status}
    if clear_error:
        updates['error_message'] = None
    elif error_message is not None:
        updates['error_message'] = str(error_message)[:500]
    if pages_count is not None:
        updates['pages_count'] = int(pages_count)
    if chunks_count is not None:
        updates['chunks_count'] = int(chunks_count)
    if embedded_chunks_count is not None:
        updates['embedded_chunks_count'] = int(embedded_chunks_count)
    if embedding_model is not None:
        updates['embedding_model'] = embedding_model
    if indexed_at is not None:
        updates['indexed_at'] = indexed_at

    set_parts = [f'{key} = %s' for key in updates]
    params = list(updates.values()) + [str(doc_id)]

    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                UPDATE guide_documents
                SET {', '.join(set_parts)}
                WHERE doc_id = %s
                RETURNING *
                """,
                params,
            )
            row = cursor.fetchone()
        conn.commit()
        return _row_to_document(dict(row) if row else None)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def prepare_reindex(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> dict | None:
    """Reset document counters and bump version before reindexing."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE guide_documents
                SET
                    version = version + 1,
                    status = 'pending',
                    error_message = NULL,
                    pages_count = 0,
                    chunks_count = 0,
                    embedded_chunks_count = 0,
                    embedding_model = NULL,
                    indexed_at = NULL
                WHERE doc_id = %s
                RETURNING *
                """,
                (str(doc_id),),
            )
            row = cursor.fetchone()
        conn.commit()
        return _row_to_document(dict(row) if row else None)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> bool:
    """Delete document by UUID. Returns True if a row was removed."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'DELETE FROM guide_documents WHERE doc_id = %s RETURNING doc_id',
                (str(doc_id),),
            )
            deleted = cursor.fetchone() is not None
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
