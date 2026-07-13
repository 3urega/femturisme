"""Per-request context for tool input normalization."""
from __future__ import annotations

from contextvars import ContextVar

turn_user_message: ContextVar[str] = ContextVar('turn_user_message', default='')
