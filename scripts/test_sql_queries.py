#!/usr/bin/env python3
"""Quick MySQL connectivity check for Fase 3 (see fase-3-tools-mysql-ca.md)."""
from __future__ import annotations

import argparse
import importlib.util
import sys


def _connection_module_exists() -> bool:
    return importlib.util.find_spec('app.db.connection') is not None


def ping() -> int:
    if not _connection_module_exists():
        print('MySQL connection not implemented yet (app/db/connection.py).')
        return 0

    from app.db.connection import ping_mysql  # type: ignore[import-not-found]

    ping_mysql()
    print('MySQL OK')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='SQL integration helpers')
    parser.add_argument('--ping', action='store_true', help='Test MySQL connection')
    args = parser.parse_args()

    if args.ping:
        return ping()

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
