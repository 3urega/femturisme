"""PostgreSQL repository for guide documents (admin CRUD)."""
from __future__ import annotations

import uuid
from typing import Any, Mapping

from psycopg2.extras import RealDictCursor

from app.db.connection import get_postgres_connection
from app.db.mappers import document_row_to_json


class DocumentValidationError(ValueError):
    """Invalid document field values before hitting the database."""


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
