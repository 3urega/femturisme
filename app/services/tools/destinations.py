"""Tool: search_destinations — MySQL catalog (on anar)."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import destinations

SCHEMA = {
    'name': 'search_destinations',
    'description': (
        'Search towns, municipalities and places to visit in Catalonia or Andorra. '
        'Use for where to go, destinations to explore, comarques, villages and '
        'territorial tourism questions.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, place or comarca, e.g. "Besalú", "Girona", "Empordà"',
            },
            'region': {
                'type': 'string',
                'description': 'Optional comarca or region filter, e.g. "Garrotxa", "Berguedà"',
            },
            'lang': {
                'type': 'string',
                'description': 'Content language: ca (default), es, or en',
            },
        },
        'required': ['destination'],
    },
}


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    if not destination:
        return json.dumps({'error': 'destination required', 'results': []})

    region = tool_input.get('region', '')
    region = str(region).strip() if region is not None else ''
    region = region or None

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    try:
        data = destinations.search(
            destination=destination,
            region=region,
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
