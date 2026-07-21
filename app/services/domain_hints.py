"""Detect active establishment (sleep/dining) domain from session history."""
from __future__ import annotations

import re
from dataclasses import dataclass

_HISTORY_WINDOW = 8

_ESTABLISHMENT_FOLLOWUP_PATTERNS = (
    r'\b\d+\s*(?:o|u)\s*\d+\s*(?:m[eé]s|mesos)\b',
    r'\b(?:m[eé]s|mesos)\s+(?:opcions?|allotjaments?|hotels?|restaurants?)\b',
    r'\bno\s+cal\b.*\b(?:rurals?|cases?\s*rurals?)\b',
    r"^\s*(?:si|sí|ok|vale|d'acord|endavant|perfecte)\s*[!.?,]*\s*$",
    r'^\s*(?:si\s+us\s+plau|siusplau|gràcies|gracies|merci)\s*[!.?,]*\s*$',
)

_ESTABLISHMENT_QUERY_PATTERNS = (
    r'\bon dormir\b',
    r'\bon menjar\b',
    r'\ballotjament\b',
    r'\balojamiento\b',
    r'\baccommodation\b',
    r'\bhotel\b',
    r'\bhostal\b',
    r'\bcamping\b',
    r'\brestaurant\b',
    r'\bmenjar\b',
    r'\ba prop de\b',
    r'\bprop de\b',
    r'\bals voltants\b',
    r'\bvoltants de\b',
)

_EXPERIENCE_INTENT_PATTERNS = (
    r'\bvisites?\s+guiades?\b',
    r'\bvisitas?\s+guiadas?\b',
    r'\bexperi[eè]ncia\b',
    r'\bofertes?\s+promocionals?\b',
    r'\barrossada\b',
    r'\bdinar\s+tem[aà]tic\b',
)

_KM_QUESTION_PATTERNS = (
    r'\bquants km\b',
    r'\bquants quil[oò]metres\b',
    r'\bcuants km\b',
    r'\bcuantos km\b',
    r'\bhow many km\b',
    r'\bcombien de km\b',
)

_KM_IN_MESSAGE = re.compile(r'\b(\d+)\s*km\b', re.UNICODE | re.IGNORECASE)


@dataclass(frozen=True)
class EstablishmentDomainContext:
    active: bool
    destination: str | None = None
    distance_km: int | None = None


def _normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def is_establishment_followup_message(user_message: str) -> bool:
    """True for short accommodation/dining follow-ups that must not trigger thematic fan-out."""
    text = _normalize_text(user_message)
    if not text:
        return False
    return any(
        re.search(pattern, text, flags=re.UNICODE)
        for pattern in _ESTABLISHMENT_FOLLOWUP_PATTERNS
    )


def _user_mentions_establishment(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(
        re.search(pattern, normalized)
        for pattern in _ESTABLISHMENT_QUERY_PATTERNS
    )


def _has_experience_intent(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(
        re.search(pattern, normalized)
        for pattern in _EXPERIENCE_INTENT_PATTERNS
    )


def _assistant_asked_km(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(
        re.search(pattern, normalized)
        for pattern in _KM_QUESTION_PATTERNS
    )


def _parse_distance_km(text: str) -> int | None:
    match = _KM_IN_MESSAGE.search(_normalize_text(text))
    if not match:
        return None
    try:
        value = int(match.group(1))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _capitalize_destination(destination: str) -> str:
    cleaned = destination.strip(' ?.,')
    if not cleaned:
        return cleaned
    return cleaned[:1].upper() + cleaned[1:]


def _infer_destination_from_message(text: str) -> str | None:
    normalized = _normalize_text(text)
    if not normalized:
        return None

    for pattern in (
        r'\b(?:a prop de|prop de|als voltants de|voltants de|des de|des d\'?)\s+'
        r"([a-zàèéíòóúç][a-zàèéíòóúç\s\-']{1,})",
        r"\b(?:a|al|a l'|en)\s+([a-zàèéíòóúç][a-zàèéíòóúç\s\-']{2,})",
        r'\bde\s+([a-zàèéíòóúç][a-zàèéíòóúç\s\-']{2,})',
    ):
        match = re.search(pattern, normalized)
        if match:
            destination = _capitalize_destination(match.group(1))
            stop_words = {
                'aquest', 'aquesta', 'este', 'esta', 'this', 'mes', 'cap', 'setmana',
                'allotjament', 'allotjaments', 'hotel', 'hotels', 'restaurant',
            }
            first = destination.split()[0].lower() if destination else ''
            if destination and first not in stop_words:
                return destination
    return None


def _assistant_text(content: object) -> str:
    if isinstance(content, str):
        return content
    return ''


def _iter_tool_uses(history: list[dict]) -> list[tuple[str, dict]]:
    found: list[tuple[str, dict]] = []
    for msg in history:
        if msg.get('role') != 'assistant':
            continue
        content = msg.get('content')
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use':
                tool_input = block.get('input')
                found.append((
                    str(block.get('name') or ''),
                    dict(tool_input) if isinstance(tool_input, dict) else {},
                ))
    return found


def _is_domain_continuation(user_message: str) -> bool:
    text = _normalize_text(user_message)
    if not text:
        return False
    if is_establishment_followup_message(user_message):
        return True
    if _parse_distance_km(text) is not None:
        return True
    if re.fullmatch(r'(?:si|sí)[!.?,]*', text):
        return True
    if re.search(r'\b(?:si|sí)\b', text) and _parse_distance_km(text) is not None:
        return True
    return False


def _scan_history_signals(history: list[dict]) -> tuple[bool, bool, bool, str | None, int | None]:
    """Return signal_a, signal_b, signal_c, destination, distance_km_from_tool."""
    window = history[-_HISTORY_WINDOW:] if history else []
    signal_a = False
    signal_b = False
    signal_c = False
    destination: str | None = None
    distance_km_from_tool: int | None = None

    for name, tool_input in reversed(_iter_tool_uses(window)):
        if name != 'search_establishments':
            continue
        signal_c = True
        if tool_input.get('destination') and not destination:
            destination = str(tool_input['destination'])
        parsed_km = tool_input.get('distance_km')
        if parsed_km is not None and distance_km_from_tool is None:
            try:
                distance_km_from_tool = int(parsed_km)
            except (TypeError, ValueError):
                pass

    for index in range(len(window) - 1, -1, -1):
        msg = window[index]
        role = msg.get('role')

        if role == 'user' and isinstance(msg.get('content'), str):
            user_text = msg['content']
            if _user_mentions_establishment(user_text):
                signal_a = True
                if not destination:
                    destination = _infer_destination_from_message(user_text)

        if role == 'assistant':
            assistant_text = _assistant_text(msg.get('content'))
            if not assistant_text or not _assistant_asked_km(assistant_text):
                continue
            for prev in reversed(window[:index]):
                if prev.get('role') != 'user' or not isinstance(prev.get('content'), str):
                    continue
                if _user_mentions_establishment(prev['content']):
                    signal_b = True
                    if not destination:
                        destination = _infer_destination_from_message(prev['content'])
                break

    return signal_a, signal_b, signal_c, destination, distance_km_from_tool


def infer_establishment_domain_context(
    history: list[dict],
    user_message: str,
) -> EstablishmentDomainContext:
    """Infer whether the active dialog domain is establishments from history + current turn."""
    text = _normalize_text(user_message)

    if _has_experience_intent(text) and not _user_mentions_establishment(text):
        return EstablishmentDomainContext(active=False)

    if not _is_domain_continuation(user_message):
        return EstablishmentDomainContext(active=False)

    signal_a, signal_b, signal_c, destination, distance_km_from_tool = _scan_history_signals(history)
    if not (signal_a or signal_b or signal_c):
        return EstablishmentDomainContext(active=False)

    if not destination:
        destination = _infer_destination_from_message(user_message)
    if not destination:
        return EstablishmentDomainContext(active=False)

    distance_km = _parse_distance_km(user_message) or distance_km_from_tool

    return EstablishmentDomainContext(
        active=True,
        destination=destination,
        distance_km=distance_km,
    )


def is_establishment_domain_active(
    history: list[dict],
    user_message: str,
) -> bool:
    return infer_establishment_domain_context(history, user_message).active


def build_establishment_turn_instruction(ctx: EstablishmentDomainContext) -> str:
    """Build per-turn system prompt block when establishment domain is active."""
    parts = [
        "\n\n## Instrucció d'aquest torn\n",
        "El diàleg va sobre allotjament/menjar. **Has de cridar només `search_establishments`**",
    ]
    if ctx.destination:
        parts.append(f"amb `destination: {ctx.destination}`")
    if ctx.distance_km is not None:
        parts.append(f"i `distance_km: {ctx.distance_km}`")
    parts.append("(sense `type` genèric).")
    parts.append(
        "**No** cridis `search_experiences`, `search_articles` ni `search_events`.\n"
    )
    return ' '.join(parts)
