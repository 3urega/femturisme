"""PostgreSQL schema integration tests (DEV-500)."""
from __future__ import annotations

import pytest

from tests.helpers.env import postgres_available


@pytest.mark.integration
@pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured')
def test_vector_extension_installed():
    from app.db.connection import get_postgres_connection

    conn = get_postgres_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == 'vector'
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured')
def test_rag_tables_exist():
    from app.db.connection import get_postgres_connection

    expected = {'entities', 'guide_documents', 'document_chunks'}
    conn = get_postgres_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s)
                """,
                (list(expected),),
            )
            found = {row[0] for row in cursor.fetchall()}
        assert found == expected
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured')
def test_enum_types_exist():
    from app.db.connection import get_postgres_connection

    expected = {'entity_type', 'guide_document_status'}
    conn = get_postgres_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT typname
                FROM pg_type
                WHERE typname = ANY(%s)
                  AND typtype = 'e'
                """,
                (list(expected),),
            )
            found = {row[0] for row in cursor.fetchall()}
        assert found == expected
    finally:
        conn.close()


@pytest.mark.integration
@pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured')
def test_embedding_column_is_vector_1536():
    from app.db.connection import get_postgres_connection

    conn = get_postgres_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT format_type(a.atttypid, a.atttypmod)
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname = 'document_chunks'
                  AND a.attname = 'embedding'
                  AND NOT a.attisdropped
                """
            )
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == 'vector(1536)'
    finally:
        conn.close()
