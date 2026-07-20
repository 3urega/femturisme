#!/usr/bin/env python3
"""Apply agent PostgreSQL schema (DEV-500). Idempotent — safe to re-run."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv()

SCHEMA_PATH = _ROOT / 'docs' / 'schema-agent-postgres.sql'


def _strip_sql_comments(text: str) -> str:
    lines = [line for line in text.splitlines() if not line.strip().startswith('--')]
    return '\n'.join(lines).strip()


def _split_sql_statements(sql: str) -> list[str]:
    """Split DDL into executable statements, respecting quotes and dollar quotes."""
    statements: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(sql)
    dollar_tag: str | None = None
    in_single_quote = False

    while i < n:
        ch = sql[i]

        if in_single_quote:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    buf.append(sql[i + 1])
                    i += 2
                    continue
                in_single_quote = False
            i += 1
            continue

        if dollar_tag is not None:
            close = f'${dollar_tag}$'
            if sql.startswith(close, i):
                buf.append(close)
                i += len(close)
                dollar_tag = None
                continue
            buf.append(ch)
            i += 1
            continue

        if ch == "'":
            in_single_quote = True
            buf.append(ch)
            i += 1
            continue

        if ch == '$':
            j = i + 1
            while j < n and sql[j] != '$':
                j += 1
            if j < n:
                tag = sql[i + 1:j]
                dollar_tag = tag
                buf.append(sql[i:j + 1])
                i = j + 1
                continue

        if ch == ';':
            stmt = _strip_sql_comments(''.join(buf))
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = _strip_sql_comments(''.join(buf))
    if tail:
        statements.append(tail)
    return statements


def _check_vector_extension(cursor) -> None:
    cursor.execute(
        "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
    )
    if cursor.fetchone() is None:
        raise RuntimeError(
            'pgvector extension is not installed. '
            'Enable the "vector" extension on your PostgreSQL instance '
            '(Neon/Supabase: enable in dashboard; then re-run this script).'
        )


def _verify_schema(cursor) -> dict[str, bool]:
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN ('entities', 'guide_documents', 'document_chunks')
        """
    )
    tables = {row[0] for row in cursor.fetchall()}
    required = {'entities', 'guide_documents', 'document_chunks'}
    return {name: name in tables for name in required}


def apply_schema() -> int:
    from app.db.connection import DatabaseError, get_postgres_connection, ping_postgres

    ping = ping_postgres()
    if ping.get('status') == 'not_configured':
        print(
            'PostgreSQL not configured. Set POSTGRES_HOST, POSTGRES_USER, '
            'POSTGRES_PASSWORD, POSTGRES_DATABASE in .env',
            file=sys.stderr,
        )
        return 1
    if ping.get('status') != 'ok':
        print(f"PostgreSQL connection failed: {ping.get('error', 'unknown')}", file=sys.stderr)
        return 1

    if not SCHEMA_PATH.is_file():
        print(f'Schema file not found: {SCHEMA_PATH}', file=sys.stderr)
        return 1

    sql = SCHEMA_PATH.read_text(encoding='utf-8')
    statements = _split_sql_statements(sql)
    print(f'Applying schema from {SCHEMA_PATH.name} ({len(statements)} statements)...')

    conn = None
    try:
        conn = get_postgres_connection()
        conn.autocommit = True
        with conn.cursor() as cursor:
            for i, stmt in enumerate(statements, start=1):
                try:
                    cursor.execute(stmt)
                except Exception as exc:
                    preview = stmt[:80].replace('\n', ' ')
                    print(f'Statement {i} failed: {preview}...', file=sys.stderr)
                    raise exc

            _check_vector_extension(cursor)
            tables = _verify_schema(cursor)

        missing = [name for name, ok in tables.items() if not ok]
        if missing:
            print(f'Schema incomplete — missing tables: {", ".join(missing)}', file=sys.stderr)
            return 1

        print('Schema applied successfully.')
        print('  extension: vector')
        print('  tables: entities, guide_documents, document_chunks')
        print('  enums: entity_type, guide_document_status')
        print('  index: idx_document_chunks_embedding_hnsw (HNSW)')
        return 0
    except DatabaseError as exc:
        print(f'Database error: {exc}', file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()


def main() -> int:
    return apply_schema()


if __name__ == '__main__':
    raise SystemExit(main())
