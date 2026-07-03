"""Tool: search_routes — scrapes /rutes on femturisme.cat."""
import json
from .scraper import fetch_page, extract_cards, result_count

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
        },
        'required': ['destination'],
    },
}

_TYPE_MAP = {
    'hiking':    'A peu',
    'walking':   'A peu',
    'peu':       'A peu',
    'culture':   'Cultura',
    'cultural':  'Cultura',
    'cycling':   'En bicicleta',
    'bike':      'En bicicleta',
    'bicicleta': 'En bicicleta',
    'adventure': 'Esports i aventura',
    'sport':     'Esports i aventura',
    'gastro':    'Gastronomia',
    'food':      'Gastronomia',
    'history':   'Història',
    'historia':  'Història',
    'nature':    'Natura',
    'natura':    'Natura',
    'literary':  'Literària',
}


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    route_type  = tool_input.get('type', '').lower().strip()

    params: dict = {}
    if destination:
        params['ubicacio'] = destination
    if route_type:
        params['tipus'] = _TYPE_MAP.get(route_type, route_type)

    soup = fetch_page('/rutes', params)
    if not soup:
        return json.dumps({'error': 'No s\'ha pogut accedir a femturisme.cat', 'results': []})

    cards = extract_cards(soup, limit=6)
    count = result_count(soup)

    return json.dumps({
        'destination': destination,
        'type':        tool_input.get('type'),
        'total':       count,
        'results':     cards,
    }, ensure_ascii=False)
