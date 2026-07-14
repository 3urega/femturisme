"""Tool: search_articles — MySQL catalog (articles / notícies)."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import articles

SCHEMA = {
    'name': 'search_articles',
    'description': (
        'Search editorial articles and news about towns, events, natural parks '
        'and tourism topics on femturisme.cat. Use for news, notícies, articles '
        'about a place or theme — not calendar agenda (use search_events).'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Optional town or comarca related to the article, e.g. "Berga", "Empordà"',
            },
            'topic': {
                'type': 'string',
                'description': 'Optional theme, e.g. "Parc Natural del Cadí", "Patum de Berga"',
            },
            'query': {
                'type': 'string',
                'description': 'Optional short free-text search in title or body',
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


def execute(tool_input: dict) -> str:
    destination = _normalize_optional(tool_input.get('destination'))
    topic = _normalize_optional(tool_input.get('topic'))
    query = _normalize_optional(tool_input.get('query'))

    if not any((destination, topic, query)):
        return json.dumps(
            {
                'error': 'At least one of destination, topic or query is required',
                'results': [],
            },
            ensure_ascii=False,
        )

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    try:
        data = articles.search(
            destination=destination,
            topic=topic,
            query=query,
            lang=lang,
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
