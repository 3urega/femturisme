"""PostgreSQL repository for RAG entities (admin CRUD)."""
from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from psycopg2 import errors as pg_errors
from psycopg2.extras import RealDictCursor

from app.db.connection import DatabaseError, get_postgres_connection
from app.db.mappers import entity_row_to_json

ENTITY_TYPES = frozenset({
    'ajuntament',
    'diputacio',
    'poblacio',
    'museu',
    'fira',
    'establiment',
    'oficina_turisme',
    'club',
    'altres',
})

_UPDATABLE_FIELDS = frozenset({
    'name',
    'entity_type',
    'slug',
    'territory',
    'config',
    'is_active',
})


class EntityValidationError(ValueError):
    """Invalid entity field values before hitting the database."""


class DuplicateSlugError(Exception):
    """Raised when slug violates entities_slug_unique."""


def _validate_entity_type(entity_type: str) -> str:
    value = str(entity_type or '').strip()
    if value not in ENTITY_TYPES:
        supported = ', '.join(sorted(ENTITY_TYPES))
        raise EntityValidationError(
            f'Invalid entity_type={value!r}; expected one of: {supported}'
        )
    return value


def _validate_name(name: str) -> str:
    value = str(name or '').strip()
    if not value:
        raise EntityValidationError('name is required')
    return value


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_config(config: dict | None) -> dict:
    if config is None:
        return {}
    if not isinstance(config, dict):
        raise EntityValidationError('config must be a JSON object')
    return config


def _row_to_entity(row: dict | None) -> dict | None:
    if row is None:
        return None
    return entity_row_to_json(dict(row))


def create(
    *,
    name: str,
    entity_type: str,
    slug: str | None = None,
    territory: str | None = None,
    config: dict | None = None,
    config_mapping: Mapping[str, Any] | None = None,
) -> dict:
    """Insert an entity and return the full row as admin JSON."""
    validated_name = _validate_name(name)
    validated_type = _validate_entity_type(entity_type)
    normalized_slug = _normalize_optional_text(slug)
    normalized_territory = _normalize_optional_text(territory)
    normalized_config = _normalize_config(config)

    conn = get_postgres_connection(config_mapping)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO entities (name, entity_type, slug, territory, config)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    validated_name,
                    validated_type,
                    normalized_slug,
                    normalized_territory,
                    json.dumps(normalized_config),
                ),
            )
            row = cursor.fetchone()
        conn.commit()
        return _row_to_entity(row)
    except pg_errors.UniqueViolation as exc:
        conn.rollback()
        if exc.diag.constraint_name == 'entities_slug_unique':
            raise DuplicateSlugError(f'slug already exists: {normalized_slug!r}') from exc
        raise DatabaseError(str(exc)) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_active(*, config: Mapping[str, Any] | None = None) -> list[dict]:
    """Return active entities ordered by name."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM entities
                WHERE is_active = true
                ORDER BY name
                """
            )
            rows = cursor.fetchall()
        return [_row_to_entity(dict(row)) for row in rows]
    finally:
        conn.close()


def get_by_id(entity_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> dict | None:
    """Return one entity by UUID or None if missing."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT * FROM entities WHERE entity_id = %s',
                (str(entity_id),),
            )
            row = cursor.fetchone()
        return _row_to_entity(dict(row) if row else None)
    finally:
        conn.close()


def update(
    entity_id: str | uuid.UUID,
    *,
    fields: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> dict | None:
    """Partial update; returns updated entity or None if not found."""
    updates: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in _UPDATABLE_FIELDS:
            continue
        if key == 'name':
            updates[key] = _validate_name(value)
        elif key == 'entity_type':
            updates[key] = _validate_entity_type(value)
        elif key in ('slug', 'territory'):
            updates[key] = _normalize_optional_text(value)
        elif key == 'config':
            updates[key] = _normalize_config(value)
        elif key == 'is_active':
            updates[key] = bool(value)

    if not updates:
        return get_by_id(entity_id, config=config)

    set_parts = []
    params: list[Any] = []
    for key, value in updates.items():
        if key == 'config':
            set_parts.append('config = %s::jsonb')
            params.append(json.dumps(value))
        else:
            set_parts.append(f'{key} = %s')
            params.append(value)
    params.append(str(entity_id))

    conn = get_postgres_connection(config)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"""
                UPDATE entities
                SET {', '.join(set_parts)}
                WHERE entity_id = %s
                RETURNING *
                """,
                params,
            )
            row = cursor.fetchone()
        conn.commit()
        return _row_to_entity(dict(row) if row else None)
    except pg_errors.UniqueViolation as exc:
        conn.rollback()
        if exc.diag.constraint_name == 'entities_slug_unique':
            slug = updates.get('slug')
            raise DuplicateSlugError(f'slug already exists: {slug!r}') from exc
        raise DatabaseError(str(exc)) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete(entity_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> bool:
    """Delete entity by UUID. Returns True if a row was removed."""
    conn = get_postgres_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'DELETE FROM entities WHERE entity_id = %s RETURNING entity_id',
                (str(entity_id),),
            )
            deleted = cursor.fetchone() is not None
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
