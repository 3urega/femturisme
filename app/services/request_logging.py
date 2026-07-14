"""Structured request logging for chat and catalog queries (tecnic.md §13.1)."""
from __future__ import annotations

import json
import logging
from typing import Any, Mapping

logger = logging.getLogger('agent.request')

_SAFE_TOOL_PARAM_KEYS = frozenset({
    'destination',
    'lang',
    'type',
    'topic',
    'query',
    'date_from',
    'date_to',
    'establishment_type',
})


def _is_enabled() -> bool:
    try:
        from flask import current_app

        return bool(current_app.config.get('REQUEST_LOGGING_ENABLED', True))
    except RuntimeError:
        return True


def _emit(event: str, **fields: Any) -> None:
    if not _is_enabled():
        return
    payload = {'event': event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def safe_tool_params(tool_input: Mapping[str, Any]) -> dict[str, Any]:
    """Whitelist tool parameters safe for logs (no full user message)."""
    return {
        key: value
        for key, value in tool_input.items()
        if key in _SAFE_TOOL_PARAM_KEYS and not str(key).startswith('_')
    }


def log_chat_turn(
    *,
    session_id: str,
    duration_ms: float,
    language: str,
    operational_mode: str,
    entity_id: str | None = None,
    status: str = 'ok',
) -> None:
    _emit(
        'chat_turn',
        session_id=session_id,
        duration_ms=round(duration_ms, 2),
        language=language,
        operational_mode=operational_mode,
        entity_id=entity_id,
        status=status,
    )


def log_catalog_query(
    *,
    tool: str,
    params: Mapping[str, Any],
    duration_ms: float,
    total: str | int | None,
) -> None:
    _emit(
        'catalog_query',
        tool=tool,
        params=dict(params),
        duration_ms=round(duration_ms, 2),
        total=total,
    )


def log_error(
    *,
    session_id: str | None = None,
    message: str,
    error_code: str | None = None,
    exc: BaseException | None = None,
) -> None:
    if exc is not None:
        logger.error(
            json.dumps(
                {
                    'event': 'error',
                    'session_id': session_id,
                    'message': message,
                    'error_code': error_code,
                },
                ensure_ascii=False,
                default=str,
            ),
            exc_info=exc,
        )
        return
    _emit(
        'error',
        session_id=session_id,
        message=message,
        error_code=error_code,
    )
