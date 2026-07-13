"""Unit tests for app.db.mappers — issue #5 / #11."""
from __future__ import annotations

from app.db.mappers import build_search_wrapper, row_to_card, rows_to_cards


def test_row_to_card_establishment_shape():
    card = row_to_card(
        {
            'id': 1,
            'title': 'Hotel Test',
            'param_url': 'hotel-test',
            'type_code': 'on-dormir',
            'type_label': 'Hotel',
            'location': 'Girona',
            'comarca': 'Gironès',
        },
        'establishment',
    )
    assert card['title'] == 'Hotel Test'
    assert card['source_type'] == 'establishment'
    assert card['source_id'] == '1'
    assert card['url'] == 'https://www.femturisme.cat/on-dormir/hotel-test'
    assert card['location'] == 'Girona (Gironès)'


def test_row_to_card_event_date_range():
    card = row_to_card(
        {
            'id': 42,
            'title': 'Festa major',
            'param_url': 'festa-major',
            'date_start': '2026-06-28',
            'date_end': '2026-06-29',
            'location': 'Figueres',
        },
        'event',
    )
    assert card['source_type'] == 'event'
    assert card['date'] == '28/06/2026 – 29/06/2026'
    assert card['url'] == 'https://www.femturisme.cat/agenda/festa-major'


def test_row_to_card_destination():
    card = row_to_card(
        {
            'id': 7,
            'title': 'Besalú',
            'param_url': 'besalu',
            'region': 'Garrotxa',
            'description': 'Poble medieval',
        },
        'destination',
    )
    assert card['source_type'] == 'destination'
    assert card['url'] == 'https://www.femturisme.cat/besalu'
    assert card['location'] == 'Garrotxa'


def test_row_to_card_article():
    card = row_to_card(
        {
            'id': 99,
            'title': 'Parc Natural del Cadí',
            'param_url': 'parc-natural-cadi',
            'published_at': '2025-03-15',
            'location': 'La Seu d\'Urgell',
            'description': 'Article sobre el parc natural.',
        },
        'article',
    )
    assert card['source_type'] == 'article'
    assert card['source_id'] == '99'
    assert card['url'] == 'https://www.femturisme.cat/noticies/parc-natural-cadi'
    assert card['date'] == '15/03/2025'
    assert card['location'] == "La Seu d'Urgell"


def test_row_to_card_invalid_content_type():
    try:
        row_to_card({'id': 1, 'title': 'Test'}, 'unknown')
        assert False, 'expected ValueError'
    except ValueError as exc:
        assert 'unknown' in str(exc)


def test_rows_to_cards_skips_empty_title():
    cards = rows_to_cards(
        [
            {'id': 1, 'title': 'OK', 'param_url': 'ok'},
            {'id': 2, 'title': '', 'param_url': 'skip'},
            {'id': 3, 'title': None, 'param_url': 'skip2'},
        ],
        'destination',
    )
    assert len(cards) == 1
    assert cards[0]['title'] == 'OK'


def test_build_search_wrapper_error():
    payload = build_search_wrapper(
        destination='Girona',
        results=[],
        error='Database unavailable',
    )
    assert payload['total'] == '0'
    assert payload['results'] == []
    assert payload['error'] == 'Database unavailable'


def test_build_search_wrapper_success():
    results = [{'title': 'Hotel', 'url': 'https://www.femturisme.cat/x'}]
    payload = build_search_wrapper(
        destination='Girona',
        results=results,
        type='hotel',
        lang='ca',
    )
    assert payload['total'] == '1'
    assert payload['results'] == results
    assert payload['error'] is None
    assert payload['type'] == 'hotel'
    assert payload['lang'] == 'ca'
