"""Tool: search_establishments — MySQL catalog (sleep + dining)."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import establishments

SCHEMA = {
    'name': 'search_establishments',
    'description': (
        'Search tourist establishments in Catalonia or Andorra: accommodation '
        'and dining in one catalog. Use for where to sleep, where to eat, hotels, '
        'campings, restaurants, bars, rural houses, and similar by town or comarca.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Girona", "Pals", "Empordà"',
            },
            'type': {
                'type': 'string',
                'description': (
                    'Optional filter: hotel, camping, restaurant, bar, casa-rural, '
                    'hostal, apartament…'
                ),
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

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    acc_type = tool_input.get('type', '')
    acc_type = str(acc_type).strip() if acc_type is not None else ''
    acc_type = acc_type or None

    try:
        data = establishments.search(
            destination=destination,
            type=acc_type,
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
