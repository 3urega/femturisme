"""Tool: search_experiences — scrapes /ofertes on femturisme.cat."""
import json
from .scraper import fetch_page, extract_cards, result_count

SCHEMA = {
    'name': 'search_experiences',
    'description': (
        'Search tourism experiences, offers and activities in Catalonia or Andorra: '
        'guided visits, workshops, adventure sports, gastronomy, family activities, etc. '
        'Use for questions like "what to do in X", "experiences near X", "activities in X".'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Berga", "Costa Brava", "Pirineu"',
            },
            'category': {
                'type': 'string',
                'description': (
                    'Optional filter: Activitats | Allotjaments | Familiar | '
                    'Visites guiades | Escapades | Menús'
                ),
            },
        },
        'required': ['destination'],
    },
}

_CATEGORY_MAP = {
    'activitats':     'Activitats',
    'activities':     'Activitats',
    'familiar':       'Familiar',
    'family':         'Familiar',
    'visites':        'Visites guiades',
    'guided':         'Visites guiades',
    'escapades':      'Escapades',
    'escapes':        'Escapades',
    'menus':          'Menús',
    'gastronomy':     'Menús',
}


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    category    = tool_input.get('category', '').lower()

    params: dict = {}
    if destination:
        params['ubicacio'] = destination
    if category:
        params['tipus'] = _CATEGORY_MAP.get(category, category)

    soup = fetch_page('/ofertes', params)
    if not soup:
        return json.dumps({'error': 'No s\'ha pogut accedir a femturisme.cat', 'results': []})

    cards = extract_cards(soup, limit=6)
    count = result_count(soup)

    return json.dumps({
        'destination': destination,
        'category':    tool_input.get('category'),
        'total':       count,
        'results':     cards,
    }, ensure_ascii=False)
