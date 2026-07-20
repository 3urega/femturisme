"""Environment helpers for integration tests."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, *fallbacks: str) -> str:
    for key in (name, *fallbacks):
        value = os.environ.get(key, '').strip()
        if value:
            return value
    return ''


def mysql_available() -> bool:
    """True when MySQL staging credentials are configured."""
    host = _env('AGENT_MYSQL_HOST', 'MYSQL_HOST')
    user = _env('AGENT_MYSQL_USER', 'MYSQL_USER')
    return bool(host and user)


def postgres_available() -> bool:
    """True when PostgreSQL agent credentials are configured."""
    host = _env('AGENT_POSTGRES_HOST', 'POSTGRES_HOST')
    user = _env('AGENT_POSTGRES_USER', 'POSTGRES_USER')
    return bool(host and user)
