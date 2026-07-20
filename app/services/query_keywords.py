"""Extract searchable keywords from user messages for catalog recall."""
from __future__ import annotations

import re

from app.db.territory import is_broad_territory
from app.services.period_hints import (
    build_forced_search_events_input,
    infer_agenda_destination,
    infer_event_period,
    is_agenda_search_query,
)

_MIN_TOKEN_LEN = 3
_MAX_KEYWORD_TOKENS = 4

_STOPWORDS = frozenset({
    'a', 'al', 'als', 'amb', 'ara', 'article', 'articles', 'aquest', 'aquesta',
    'cap', 'com', 'con', 'de', 'del', 'dels', 'el', 'els', 'en', 'es', 'esta',
    'este', 'ets', 'fer', 'for', 'ha', 'he', 'hello', 'hi', 'hola', 'ho', 'i',
    'in', 'is', 'la', 'las', 'le', 'les', 'lo', 'los', 'mes', 'noticia',
    'noticies', 'notícia', 'notícies', 'on', 'para', 'per', 'que', 'què', 'quin',
    'quina', 'quines', 'quins', 'quan', 'recomana', 'recomanar', 'ser', 'setmana',
    'si', 'són', 'son', 'sobre', 'te', 'the', 'this', 'un', 'una', 'unes', 'uns',
    'what', 'when', 'where', 'with', 'y', 'és',
})

_DOMAIN_EXCLUSION_PATTERNS = (
    r'\bqu[eè]\s+fer\b',
    r'\bon anar\b',
    r'\bqu[eè]\s+veure\b',
    r'\bdestinacions?\b',
    r'\bvisitar\b',
    r'\bon dormir\b',
    r'\bon menjar\b',
    r'\ballotjament\b',
    r'\bhotel\b',
    r'\bhostal\b',
    r'\brestaurant\b',
    r'\brutes?\b',
    r'\bsenderisme\b',
    r'\bexperi[eè]ncia\b',
    r'\bofertes?\b',
    r'\bhola\b',
    r'\bgr[aà]cies\b',
    r'\bmerci\b',
    r'\bhello\b',
)


def _normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^\wàèéíòóúç'-]+", text, flags=re.UNICODE)
        if token
    ]


def _destination_tokens(destination: str | None) -> set[str]:
    if not destination:
        return set()
    return set(_tokenize(_normalize_text(destination)))


def extract_keyword_tokens(user_message: str) -> list[str]:
    """Return significant tokens for catalog text search, longest phrase first."""
    text = _normalize_text(user_message)
    if not text:
        return []

    destination = infer_agenda_destination(user_message)
    skip_tokens = _destination_tokens(destination)

    tokens: list[str] = []
    for token in _tokenize(text):
        if len(token) < _MIN_TOKEN_LEN:
            continue
        if token in _STOPWORDS:
            continue
        if is_broad_territory(token):
            continue
        if token in skip_tokens:
            continue
        tokens.append(token)

    return tokens[:_MAX_KEYWORD_TOKENS]


def primary_search_keyword(user_message: str) -> str | None:
    """Best single query string for search_articles / search_events."""
    tokens = extract_keyword_tokens(user_message)
    if not tokens:
        return None
    return ' '.join(tokens)


def _normalize_query(value: object) -> str:
    return _normalize_text(str(value or ''))


def _keyword_tool_payloads(user_message: str, keyword: str) -> tuple[dict, dict]:
    destination = infer_agenda_destination(user_message)
    articles_input: dict = {'query': keyword}
    events_input: dict = {'query': keyword}
    if destination and not is_broad_territory(destination):
        articles_input['destination'] = destination
        events_input['destination'] = destination
    return articles_input, events_input


def _call_already_has_keyword(tool_name: str, tool_input: dict, keyword: str) -> bool:
    normalized_keyword = _normalize_query(keyword)
    if tool_name == 'search_articles':
        for field in ('query', 'topic'):
            if _normalize_query(tool_input.get(field)) == normalized_keyword:
                return True
        return False
    if tool_name == 'search_events':
        return _normalize_query(tool_input.get('query')) == normalized_keyword
    return False


def _fallback_already_applied(executed: list[tuple[str, dict]]) -> bool:
    return any(tool_input.get('_keyword_fallback_applied') for _, tool_input in executed)


def _matches_domain_exclusion(user_message: str) -> bool:
    text = _normalize_text(user_message)
    return any(
        re.search(pattern, text)
        for pattern in _DOMAIN_EXCLUSION_PATTERNS
    )


def should_force_keyword_search(user_message: str) -> bool:
    """True when server-side keyword fan-out should run (path B)."""
    if len((user_message or '').strip()) < 8:
        return False
    if is_agenda_search_query(user_message):
        return False
    if build_forced_search_events_input(user_message):
        return False
    if infer_event_period(user_message) is not None:
        return False
    if _matches_domain_exclusion(user_message):
        return False
    return primary_search_keyword(user_message) is not None


def build_forced_keyword_tool_calls(
    user_message: str,
) -> list[tuple[str, dict]] | None:
    """
    Build search_articles + search_events payloads for thematic queries.

    Returns None when agenda force (path A) applies or no keyword found.
    """
    if is_agenda_search_query(user_message):
        return None
    if build_forced_search_events_input(user_message):
        return None
    if infer_event_period(user_message) is not None:
        return None
    if not should_force_keyword_search(user_message):
        return None

    keyword = primary_search_keyword(user_message)
    if not keyword:
        return None

    articles_input, events_input = _keyword_tool_payloads(user_message, keyword)

    return [
        ('search_articles', articles_input),
        ('search_events', events_input),
    ]


def build_keyword_fallback_calls(
    user_message: str,
    executed: list[tuple[str, dict]],
) -> list[tuple[str, dict]] | None:
    """
    Build reactive fallback calls when a catalog tool returned total=0.

    Skips tools already invoked with the same keyword query.
    """
    if _fallback_already_applied(executed):
        return None

    keyword = primary_search_keyword(user_message)
    if not keyword:
        return None

    articles_input, events_input = _keyword_tool_payloads(user_message, keyword)
    fallback_calls: list[tuple[str, dict]] = []

    articles_done = any(
        tool_name == 'search_articles'
        and _call_already_has_keyword(tool_name, tool_input, keyword)
        for tool_name, tool_input in executed
    )
    if not articles_done:
        fallback_calls.append(
            ('search_articles', {**articles_input, '_keyword_fallback_applied': True}),
        )

    events_done = any(
        tool_name == 'search_events'
        and _call_already_has_keyword(tool_name, tool_input, keyword)
        for tool_name, tool_input in executed
    )
    if not events_done:
        fallback_calls.append(
            ('search_events', {**events_input, '_keyword_fallback_applied': True}),
        )

    if not fallback_calls:
        return None
    return fallback_calls
