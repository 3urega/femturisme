"""Tool: search_accommodations — scrapes /on-dormir on femturisme.cat."""
import json
from .scraper import fetch_page, extract_cards, result_count

SCHEMA = {
    'name': 'search_accommodations',
    'description': (
        'Search hotels, rural houses, hostels, campings and other accommodations '
        'in Catalonia or Andorra. Use for questions about where to sleep or stay.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'destination': {
                'type': 'string',
                'description': 'Town, comarca or region, e.g. "Berga", "Vall d\'Aran", "Girona"',
            },
            'type': {
                'type': 'string',
                'description': 'Optional filter: hotel | casa-rural | hostal | camping | apartament',
            },
        },
        'required': ['destination'],
    },
}


def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    acc_type    = tool_input.get('type', '').strip()

    params: dict = {}
    if destination:
        params['ubicacio'] = destination
    if acc_type:
        params['tipus'] = acc_type

    soup = fetch_page('/on-dormir', params)
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
