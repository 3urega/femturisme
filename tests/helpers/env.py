"""Environment helpers for integration tests."""
from __future__ import annotations

import os


def mysql_available() -> bool:
    """True when MySQL staging credentials are configured."""
    host = os.environ.get('AGENT_MYSQL_HOST') or os.environ.get('MYSQL_HOST')
    user = os.environ.get('AGENT_MYSQL_USER') or os.environ.get('MYSQL_USER')
    return bool(host and user)
