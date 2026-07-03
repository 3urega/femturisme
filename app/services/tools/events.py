"""Tool: search_events — scrapes /agenda on femturisme.cat."""
import json
from .scraper import fetch_page, extract_cards, result_count

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
    date_from   = tool_input.get('date_from', '').strip()
    date_to     = tool_input.get('date_to', '').strip()

    params: dict = {}
    if destination:
        params['ubicacio'] = destination
    if date_from:
        params['data_inici'] = date_from
    if date_to:
        params['data_fi'] = date_to

    soup = fetch_page('/agenda', params)
    if not soup:
        return json.dumps({'error': 'No s\'ha pogut accedir a femturisme.cat', 'results': []})

    cards = extract_cards(soup, limit=6)
    count = result_count(soup)

    # Events store date in the 'location' field (ft-card__loc holds date range)
    for c in cards:
        if c.get('location') and not c.get('date'):
            c['date']     = c.pop('location')
            c['location'] = None

    return json.dumps({
        'destination': destination,
        'date_from':   date_from or None,
        'date_to':     date_to or None,
        'total':       count,
        'results':     cards,
    }, ensure_ascii=False)
