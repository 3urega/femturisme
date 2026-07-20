#!/usr/bin/env python3
"""CLI ingest for RAG guide PDFs without HTTP (issue #34).

Examples:
  python scripts/ingest_pdf.py --list
  python scripts/ingest_pdf.py --file guia.pdf --entity-id UUID --title "Guia"
  python scripts/ingest_pdf.py --verify DOC_ID --query "on aparcar"
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]

from app.config import Config
from app.db.repositories import documents as documents_repo
from app.db.repositories import entities as entities_repo
from app.services.document_storage import build_storage_path, save_original, validate_pdf
from app.services.indexing_pipeline import run

_CONFIG_KEYS = (
    'POSTGRES_HOST',
    'POSTGRES_PORT',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DATABASE',
    'POSTGRES_CONNECT_TIMEOUT',
    'POSTGRES_SSLMODE',
    'STORAGE_BACKEND',
    'DOCUMENT_STORAGE_PATH',
    'S3_ENDPOINT',
    'S3_REGION',
    'S3_BUCKET',
    'S3_ACCESS_KEY_ID',
    'S3_SECRET_ACCESS_KEY',
    'OPENAI_API_KEY',
    'EMBEDDING_MODEL',
)


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / '.env')


def _pipeline_config() -> dict:
    return {key: getattr(Config, key) for key in _CONFIG_KEYS}


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _line(cells: list[str]) -> str:
        return '  '.join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    print(_line(headers))
    print(_line(['-' * width for width in widths]))
    for row in rows:
        print(_line(row))


def cmd_list(_args: argparse.Namespace) -> int:
    rows = documents_repo.list_all(config=_pipeline_config())
    if not rows:
        print('No documents found.')
        return 0

    table_rows = [
        [
            str(row.get('doc_id', '')),
            str(row.get('title', '')),
            str(row.get('status', '')),
            str(row.get('entity_id', '')),
        ]
        for row in rows
    ]
    _print_table(['doc_id', 'title', 'status', 'entity_id'], table_rows)
    return 0


def cmd_file(args: argparse.Namespace) -> int:
    pdf_path = Path(args.file)
    if not pdf_path.is_file():
        print(f'File not found: {pdf_path}', file=sys.stderr)
        return 1

    entity_id = str(args.entity_id).strip()
    title = str(args.title).strip()
    if not entity_id or not title:
        print('--entity-id and --title are required with --file', file=sys.stderr)
        return 1

    config = _pipeline_config()
    entity = entities_repo.get_by_id(entity_id, config=config)
    if entity is None:
        print(f'Entity not found: {entity_id}', file=sys.stderr)
        return 1
    if entity.get('is_active') is False:
        print('Entity is not active', file=sys.stderr)
        return 1

    file_data = pdf_path.read_bytes()
    validate_pdf(file_data, 'application/pdf')

    doc_id = uuid.uuid4()
    storage_path = build_storage_path(doc_id, config=config)
    document = documents_repo.create(
        doc_id=doc_id,
        entity_id=entity_id,
        title=title,
        category=args.category,
        source_filename=pdf_path.name,
        storage_path=storage_path,
        config=config,
    )
    save_original(doc_id, file_data, config=config)

    if args.reindex:
        run(doc_id, reindex=True, config=config)
    else:
        run(doc_id, config=config)

    updated = documents_repo.get_by_id(doc_id, config=config) or document
    print(f"doc_id={updated['doc_id']} status={updated.get('status')} version={updated.get('version')}")
    if updated.get('error_message'):
        print(f"error={updated['error_message']}", file=sys.stderr)
        return 1
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    doc_id = str(args.verify).strip()
    query = str(args.query or '').strip()
    if not query:
        print('--query is required with --verify', file=sys.stderr)
        return 1

    config = _pipeline_config()
    document = documents_repo.get_by_id(doc_id, config=config)
    if document is None:
        print(f'Document not found: {doc_id}', file=sys.stderr)
        return 1

    if args.reindex:
        run(doc_id, reindex=True, config=config)
        document = documents_repo.get_by_id(doc_id, config=config) or document

    if document.get('status') != 'indexed' and not args.reindex:
        print(
            f"Document status is {document.get('status')}; use --reindex to index first.",
            file=sys.stderr,
        )
        return 1

    result = documents_repo.search(
        query=query,
        entity_id=document['entity_id'],
        doc_id=doc_id,
        category=args.category,
        config=config,
    )
    print(f"total={result['total']}")
    for index, hit in enumerate(result['results'], start=1):
        summary = hit.get('summary') or hit.get('content', '')[:120]
        print(f"{index}. distance={hit.get('distance')} summary={summary}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='RAG PDF ingest CLI (issue #34)')
    parser.add_argument('--list', action='store_true', help='List all guide documents')
    parser.add_argument('--file', metavar='PATH', help='Upload and index a PDF file')
    parser.add_argument('--entity-id', help='Entity UUID for --file')
    parser.add_argument('--title', help='Document title for --file')
    parser.add_argument('--category', help='Optional document category')
    parser.add_argument('--verify', metavar='DOC_ID', help='Run semantic search smoke test')
    parser.add_argument('--query', help='Search query for --verify')
    parser.add_argument(
        '--reindex',
        action='store_true',
        help='Reindex before verify or after upload (--file)',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _load_env()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        return cmd_list(args)
    if args.file:
        return cmd_file(args)
    if args.verify:
        return cmd_verify(args)

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
