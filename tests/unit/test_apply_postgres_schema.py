"""Unit tests for apply_postgres_schema SQL parsing."""
from __future__ import annotations

from scripts.apply_postgres_schema import _split_sql_statements


def test_split_preserves_do_block_as_single_statement():
    sql = """
    CREATE EXTENSION IF NOT EXISTS vector;

    DO $$
    BEGIN
        CREATE TYPE entity_type AS ENUM ('a');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;

    CREATE TABLE IF NOT EXISTS entities (id INT);
    """
    statements = _split_sql_statements(sql)
    assert len(statements) == 3
    assert statements[0].startswith('CREATE EXTENSION')
    assert 'DO $$' in statements[1]
    assert 'duplicate_object' in statements[1]
    assert statements[2].startswith('CREATE TABLE IF NOT EXISTS entities')


def test_split_strips_line_comments():
    sql = """
    -- comment only
    CREATE INDEX IF NOT EXISTS idx_test ON entities (entity_type);
    """
    statements = _split_sql_statements(sql)
    assert len(statements) == 1
    assert 'idx_test' in statements[0]


def test_split_preserves_semicolon_inside_single_quoted_comment():
    sql = """
    COMMENT ON COLUMN guide_documents.entity_id IS
        'Entitat propietària; filtre principal per RAG en mode entitat.';
    CREATE INDEX IF NOT EXISTS idx_x ON guide_documents (entity_id);
    """
    statements = _split_sql_statements(sql)
    assert len(statements) == 2
    assert 'Entitat propietària; filtre' in statements[0]
    assert statements[1].startswith('CREATE INDEX')
