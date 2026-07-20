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
