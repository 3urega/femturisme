#!/usr/bin/env python3
"""Quick MySQL/PostgreSQL connectivity check for Fase 3 (see fase-3-tools-mysql-ca.md)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv()


def _format_ping(label: str, result: dict) -> str:
    status = result.get('status', 'unknown')
    if status == 'not_configured':
        return f'{label}: not_configured'
    if status == 'ok':
        return f'{label}: ok'
    if status == 'error':
        return f"{label}: error — {result.get('error', 'unknown error')}"
    return f'{label}: {status}'


def ping() -> int:
    from app.db.connection import ping_mysql, ping_postgres

    mysql_result = ping_mysql()
    postgres_result = ping_postgres()

    print(_format_ping('MySQL', mysql_result))
    print(_format_ping('PostgreSQL', postgres_result))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='SQL integration helpers')
    parser.add_argument('--ping', action='store_true', help='Test MySQL and PostgreSQL connections')
    args = parser.parse_args()

    if args.ping:
        return ping()

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
