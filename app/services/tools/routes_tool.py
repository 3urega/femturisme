"""Tool: search_routes — MySQL catalog (itineraris / rutes)."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import routes

SCHEMA = {
    'name': 'search_routes',
    'description': (
        'Search hiking, cycling, cultural and other routes in Catalonia or Andorra. '
        'Use for questions about trails, walks, bike routes, scenic drives, or '
        'cultural itineraries.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Berga", "Empordà", "Pirineu"',
            },
            'type': {
                'type': 'string',
                'description': (
                    'Optional filter: A peu | Cultura | En bicicleta | '
                    'Esports i aventura | Gastronomia | Història | Natura | Literària'
                ),
            },
            'lang': {
                'type': 'string',
                'description': 'Content language: ca (default), es, en, or fr',
            },
        },
        'required': ['destination'],
    },
}

_TYPE_MAP = {
    'hiking': 'A peu',
    'walking': 'A peu',
    'peu': 'A peu',
    'culture': 'Cultura',
    'cultural': 'Cultura',
    'cycling': 'En bicicleta',
    'bike': 'En bicicleta',
    'bicicleta': 'En bicicleta',
    'adventure': 'Esports i aventura',
    'sport': 'Esports i aventura',
    'gastro': 'Gastronomia',
    'food': 'Gastronomia',
    'history': 'Història',
    'historia': 'Història',
    'nature': 'Natura',
    'natura': 'Natura',
    'literary': 'Literària',
}


def _normalize_route_type(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _TYPE_MAP.get(text.lower(), text)


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    if not destination:
        return json.dumps({'error': 'destination required', 'results': []})

    route_type = _normalize_route_type(tool_input.get('type'))

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    try:
        data = routes.search(
            destination=destination,
            type=route_type,
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
