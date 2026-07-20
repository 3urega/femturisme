"""Tool: search_events — MySQL agenda catalog."""
from __future__ import annotations

import calendar
import json
from datetime import date, timedelta

from app.db.connection import DatabaseError
from app.db.repositories import events

SCHEMA = {
    'name': 'search_events',
    'description': (
        'Search upcoming events, festivals, fairs, concerts and local activities '
        'in Catalonia or Andorra. Use for questions about agenda, what\'s on, '
        'festivals, or things happening in a specific place or period. '
        'Use query for event names or themes when the place is unknown '
        '(e.g. "Patum", "Fira medieval", "calçotada").'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': (
                    'Optional town, comarca or region, e.g. "Berga", "Barcelona", '
                    '"Tarragona"'
                ),
            },
            'query': {
                'type': 'string',
                'description': (
                    'Optional short free-text search in event title or description, '
                    'e.g. "Patum", "Fira medieval", "calçotada"'
                ),
            },
            'date_from': {
                'type': 'string',
                'description': 'Start date YYYY-MM-DD (optional)',
            },
            'date_to': {
                'type': 'string',
                'description': 'End date YYYY-MM-DD (optional)',
            },
            'lang': {
                'type': 'string',
                'description': 'Content language: ca (default), es, en, or fr',
            },
        },
        'required': [],
    },
}


def _normalize_optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_date(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _default_date_window(*, has_query: bool) -> tuple[str, str]:
    today = date.today()
    if has_query:
        date_to = today + timedelta(days=365)
        return today.isoformat(), date_to.isoformat()
    date_from = today.replace(day=1).isoformat()
    last_day = calendar.monthrange(today.year, today.month)[1]
    date_to = today.replace(day=last_day).isoformat()
    return date_from, date_to


def execute(tool_input: dict) -> str:
    destination = _normalize_optional(tool_input.get('destination'))
    query = _normalize_optional(tool_input.get('query'))

    if not destination and not query:
        return json.dumps(
            {
                'error': 'At least one of destination or query is required',
                'results': [],
            },
            ensure_ascii=False,
        )

    date_from = _normalize_date(tool_input.get('date_from'))
    date_to = _normalize_date(tool_input.get('date_to'))

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    if not date_from and not date_to:
        date_from, date_to = _default_date_window(has_query=bool(query))

    try:
        data = events.search(
            destination=destination,
            query=query,
            date_from=date_from,
            date_to=date_to,
            lang=lang,
            skip_location_filter=bool(tool_input.get('_skip_location_filter')),
            retried=bool(tool_input.get('_retried')),
        )
    except DatabaseError:
        return json.dumps(
            {
                'error': "No s'ha pogut accedir a les dades del catàleg",
                'results': [],
            },
            ensure_ascii=False,
        )

    return json.dumps(data, ensure_ascii=False)
