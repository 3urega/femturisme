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
        'campings, restaurants, bars, rural houses, and similar by town or comarca. '
        'For cuisine style or restaurant type (e.g. traditional Catalan cuisine), '
        'use type and destination without query. Use query only for specific dishes '
        'or ingredients (e.g. macarrons, paella, seafood).'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': (
                    'Town, comarca or region, e.g. "Girona", "Pals", "Empordà", '
                    '"Catalunya". Optional if query is set (defaults to Catalunya).'
                ),
            },
            'type': {
                'type': 'string',
                'description': (
                    'Optional filter: hotel, camping, restaurant, bar, '
                    'cases-rurals (casa rural / turisme rural), hostal, apartament…'
                ),
            },
            'query': {
                'type': 'string',
                'description': (
                    'Optional short free-text search in establishment name or '
                    'description for a specific dish or ingredient only (e.g. '
                    '"macarrons", "paella", "marisc"). Do not use for cuisine '
                    'styles or restaurant types (e.g. do not use for '
                    '"cuina catalana tradicional" — use type=restaurant and '
                    'destination instead).'
                ),
            },
            'lang': {
                'type': 'string',
                'description': 'Content language: ca (default), es, en, or fr',
            },
        },
        'required': [],
    },
}


_TYPE_ALIASES: dict[str, str] = {
    'casa-rural': 'cases-rurals',
    'casa rural': 'cases-rurals',
    'cases rural': 'cases-rurals',
    'cases-rural': 'cases-rurals',
    'turisme rural': 'cases-rurals',
    'turismo rural': 'cases-rurals',
    'rural tourism': 'cases-rurals',
}


def _normalize_type(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _TYPE_ALIASES.get(text.lower(), text)


def execute(tool_input: dict) -> str:
    destination = str(tool_input.get('destination') or '').strip()
    query = str(tool_input.get('query') or '').strip()

    if not destination and not query:
        return json.dumps(
            {
                'error': 'At least one of destination or query is required',
                'results': [],
            },
            ensure_ascii=False,
        )

    if not destination:
        destination = 'Catalunya'

    lang = tool_input.get('lang', 'ca')
    if lang is not None:
        lang = str(lang).strip() or 'ca'
    else:
        lang = 'ca'

    acc_type = _normalize_type(tool_input.get('type'))

    search_kwargs = {
        'destination': destination,
        'type': acc_type,
        'query': query or None,
        'lang': lang,
        'skip_location_filter': bool(tool_input.get('_skip_location_filter')),
        'retried': bool(tool_input.get('_retried')),
    }

    try:
        data = establishments.search(**search_kwargs)
        data = _apply_query_fallback(data, search_kwargs)
    except DatabaseError:
        return json.dumps(
            {
                'error': "No s'ha pogut accedir a les dades del catàleg",
                'results': [],
            },
            ensure_ascii=False,
        )

    return json.dumps(data, ensure_ascii=False)


def _apply_query_fallback(data: dict, search_kwargs: dict) -> dict:
    """
    When a text query returns no matches, attach broader results (same zone/type)
    so the LLM can recommend alternatives without inventing URLs.
    """
    query = (search_kwargs.get('query') or '').strip()
    if not query:
        return data

    try:
        total = int(data.get('total', 0) or 0)
    except (TypeError, ValueError):
        total = 0
    if total > 0 or data.get('error'):
        return data

    fallback = establishments.search(
        destination=search_kwargs['destination'],
        type=search_kwargs.get('type'),
        query=None,
        lang=search_kwargs.get('lang', 'ca'),
        skip_location_filter=search_kwargs.get('skip_location_filter', False),
        retried=search_kwargs.get('retried', False),
    )
    try:
        fallback_total = int(fallback.get('total', 0) or 0)
    except (TypeError, ValueError):
        fallback_total = 0
    if fallback_total <= 0:
        return data

    merged = dict(data)
    merged['fallback_results'] = fallback.get('results', [])
    merged['fallback_total'] = str(fallback_total)
    meta = dict(merged.get('meta') or {})
    meta['hint'] = 'zero_results_text_query'
    meta['fallback_applied'] = True
    meta['query_term'] = query
    merged['meta'] = meta
    return merged
