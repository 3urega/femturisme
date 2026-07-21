"""Tool: search_experiences — MySQL catalog (experiències promocionals)."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import experiences

SCHEMA = {
    'name': 'search_experiences',
    'description': (
        'Search promotional tourism experiences and offers linked to an establishment '
        'or town in Catalonia or Andorra: themed dinners, popular meals, family '
        'activities, guided visits, etc. Use for commercial/promotional proposals — '
        'NOT calendar agenda (use search_events for dated festivals and fairs).'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Olvan", "Berguedà", "Cerdanya"',
            },
            'category': {
                'type': 'string',
                'description': (
                    'Optional filter: Activitats | Allotjaments | Familiar | '
                    'Visites guiades | Escapades | Menús'
                ),
            },
            'establishment': {
                'type': 'string',
                'description': 'Optional establishment name filter, e.g. restaurant name',
            },
            'lang': {
                'type': 'string',
                'description': 'Content language: ca (default), es, en, or fr',
            },
            'distance_km': {
                'type': 'integer',
                'description': (
                    'Max distance in km from destination center (Haversine radius). '
                    'REQUIRED when the user mentions km or proximity with a known radius '
                    '(e.g. "50 km from Calella" → distance_km=50). '
                    'Without this parameter the search is limited to the municipality name '
                    'and often returns zero results for radius-style queries.'
                ),
            },
        },
        'required': ['destination'],
    },
}

_CATEGORY_MAP = {
    'activitats': 'Activitats',
    'activities': 'Activitats',
    'familiar': 'Familiar',
    'family': 'Familiar',
    'visites': 'Visites guiades',
    'guided': 'Visites guiades',
    'escapades': 'Escapades',
    'escapes': 'Escapades',
    'menus': 'Menús',
    'gastronomy': 'Menús',
}

_VALID_CATEGORIES = frozenset({
    'Activitats',
    'Allotjaments',
    'Bellesa i relax',
    'Cultura',
    'Escapades',
    'Esports i aventures',
    'Excursions',
    'Familiar',
    'Gastronomia',
    'Menús',
    'Restaurants',
    'Visites guiades',
})


_MAX_DISTANCE_KM = 100


def _parse_distance_km(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return min(parsed, _MAX_DISTANCE_KM)


def _normalize_category(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    mapped = _CATEGORY_MAP.get(text.lower(), text)
    if mapped not in _VALID_CATEGORIES:
        return None
    return mapped


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    if not destination:
        return json.dumps({'error': 'destination required', 'results': []})

    category = _normalize_category(tool_input.get('category'))

    establishment = tool_input.get('establishment')
    if establishment is not None:
        establishment = str(establishment).strip() or None
    else:
        establishment = None

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    try:
        data = experiences.search(
            destination=destination,
            category=category,
            establishment=establishment,
            lang=lang,
            distance_km=_parse_distance_km(tool_input.get('distance_km')),
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
