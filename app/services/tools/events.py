"""Tool: search_events — MySQL agenda catalog."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import events

SCHEMA = {
    'name': 'search_events',
    'description': (
        'Search upcoming events, festivals, fairs, concerts and local activities '
        'in Catalonia or Andorra. Use for questions about agenda, what\'s on, '
        'festivals, or things happening in a specific place or period.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Berga", "Barcelona", "Tarragona"',
            },
            'date_from': {
                'type': 'string',
                'description': 'Start date YYYY-MM-DD (optional)',
            },
            'date_to': {
                'type': 'string',
                'description': 'End date YYYY-MM-DD (optional)',
            },
        },
        'required': ['destination'],
    },
}


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    if not destination:
        return json.dumps({'error': 'destination required', 'results': []})

    date_from = tool_input.get('date_from', '')
    date_from = str(date_from).strip() if date_from is not None else ''
    date_from = date_from or None

    date_to = tool_input.get('date_to', '')
    date_to = str(date_to).strip() if date_to is not None else ''
    date_to = date_to or None

    try:
        data = events.search(
            destination=destination,
            date_from=date_from,
            date_to=date_to,
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
