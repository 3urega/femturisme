"""Parse and validate page_context / agent_context for POST /api/chat."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal

AgentMode = Literal['femturisme', 'entitat']
_VALID_MODES = frozenset({'femturisme', 'entitat'})


class ChatContextError(ValueError):
    """Invalid agent_context or page_context (HTTP 400)."""


class EntityModeNotAvailableError(RuntimeError):
    """Mode entitat requested but not implemented in Fase 1 (HTTP 501)."""


@dataclass(frozen=True)
class PageContext:
    section: str | None = None
    ubicacio: str | None = None
    municipality: str | None = None

    def has_any_field(self) -> bool:
        return bool(self.section or self.ubicacio or self.municipality)


@dataclass(frozen=True)
class AgentContext:
    mode: AgentMode = 'femturisme'
    entity_id: str | None = None


def _normalize_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_page_context(raw: object) -> PageContext | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ChatContextError('page_context must be an object')
    section = _normalize_optional_str(raw.get('section'))
    ubicacio = _normalize_optional_str(raw.get('ubicacio'))
    municipality = _normalize_optional_str(raw.get('municipality'))
    if not any((section, ubicacio, municipality)):
        return None
    return PageContext(
        section=section,
        ubicacio=ubicacio,
        municipality=municipality,
    )


def _parse_agent_context(raw: object) -> AgentContext:
    if raw is None:
        return AgentContext()
    if not isinstance(raw, dict):
        raise ChatContextError('agent_context must be an object')

    mode_raw = raw.get('mode')
    if mode_raw is None:
        mode: AgentMode = 'femturisme'
    else:
        mode_text = str(mode_raw).strip().lower()
        if mode_text not in _VALID_MODES:
            raise ChatContextError(
                f"agent_context.mode must be 'femturisme' or 'entitat'"
            )
        mode = mode_text  # type: ignore[assignment]

    entity_id = _normalize_optional_str(raw.get('entity_id'))
    return AgentContext(mode=mode, entity_id=entity_id)


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except (TypeError, ValueError) as exc:
        raise ChatContextError('agent_context.entity_id must be a valid UUID') from exc


def parse_chat_request(
    data: dict[str, Any] | None,
) -> tuple[str, str, PageContext | None, AgentContext]:
    """
    Parse POST /api/chat body.

    Returns (user_message, session_id, page_context, agent_context).
    Raises ChatContextError on invalid optional fields.
    """
    payload = data if isinstance(data, dict) else {}

    user_message = _normalize_optional_str(payload.get('message')) or ''
    session_id = _normalize_optional_str(payload.get('session_id')) or ''
    page_context = _parse_page_context(payload.get('page_context'))
    agent_context = _parse_agent_context(payload.get('agent_context'))

    return user_message, session_id, page_context, agent_context


def validate_agent_context(ctx: AgentContext) -> None:
    """Raise ChatContextError (400) or EntityModeNotAvailableError (501)."""
    if ctx.mode == 'femturisme':
        return

    if not ctx.entity_id:
        raise ChatContextError(
            'agent_context.entity_id is required when mode is entitat'
        )

    _validate_uuid(ctx.entity_id)
    raise EntityModeNotAvailableError(
        'mode entitat is not available in Fase 1; use mode femturisme'
    )
