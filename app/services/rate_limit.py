"""In-memory rate limiting for POST /api/chat (v1 single-process; P-04 Redis future)."""
from __future__ import annotations

import threading
import time
from typing import Any, Mapping

_lock = threading.Lock()
_store: dict[str, tuple[int, float]] = {}


def reset() -> None:
    """Clear counters (tests only)."""
    with _lock:
        _store.clear()


def _limits(config: Mapping[str, Any]) -> tuple[int, int, int]:
    per_ip = int(config.get('RATE_LIMIT_PER_IP', 30))
    per_session = int(config.get('RATE_LIMIT_PER_SESSION', 20))
    window = int(config.get('RATE_LIMIT_WINDOW_SECONDS', 60))
    return max(per_ip, 0), max(per_session, 0), max(window, 1)


def _consume(key: str, limit: int, window_seconds: int, now: float) -> bool:
    if limit <= 0:
        return True
    with _lock:
        count, window_start = _store.get(key, (0, now))
        if now - window_start >= window_seconds:
            count = 0
            window_start = now
        if count >= limit:
            return False
        _store[key] = (count + 1, window_start)
        return True


def check_and_consume(
    ip: str | None,
    session_id: str | None,
    config: Mapping[str, Any],
) -> bool:
    """
    Return True if the request is allowed; False if rate limit exceeded.

    Checks both IP and session buckets when limits are configured.
    """
    per_ip, per_session, window = _limits(config)
    now = time.monotonic()

    if ip and per_ip > 0:
        if not _consume(f'ip:{ip}', per_ip, window, now):
            return False

    if session_id and per_session > 0:
        if not _consume(f'session:{session_id}', per_session, window, now):
            return False

    return True
