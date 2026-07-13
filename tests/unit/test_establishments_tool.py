"""Unit tests for search_establishments tool."""
from __future__ import annotations

import json
from unittest.mock import patch

from app.services.tools.establishments import SCHEMA, execute


def test_schema_includes_query_parameter():
    props = SCHEMA['input_schema']['properties']
    assert 'query' in props
    assert 'destination' not in SCHEMA['input_schema']['required']


def test_execute_requires_destination_or_query():
    out = json.loads(execute({}))
    assert 'error' in out
    assert 'destination or query' in out['error']


def test_execute_defaults_destination_when_only_query():
    captured: dict = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return {
            'destination': kwargs['destination'],
            'total': '1',
            'results': [{'title': 'Test', 'url': 'https://example.com'}],
            'error': None,
            'query': kwargs.get('query'),
        }

    with patch(
        'app.services.tools.establishments.establishments.search',
        side_effect=fake_search,
    ):
        out = json.loads(execute({'query': 'macarrons', 'type': 'restaurant'}))

    assert captured['destination'] == 'Catalunya'
    assert captured['query'] == 'macarrons'
    assert captured['type'] == 'restaurant'
    assert out['total'] == '1'


def test_execute_passes_query_with_destination():
    calls: list[dict] = []

    def fake_search(**kwargs):
        calls.append(dict(kwargs))
        return {
            'destination': kwargs['destination'],
            'total': '1',
            'results': [{'title': 'Match', 'url': 'https://example.com'}],
            'error': None,
        }

    with patch(
        'app.services.tools.establishments.establishments.search',
        side_effect=fake_search,
    ):
        execute({
            'destination': 'Berguedà',
            'type': 'restaurant',
            'query': 'macarrons',
        })

    assert calls[0]['destination'] == 'Berguedà'
    assert calls[0]['query'] == 'macarrons'


def test_execute_query_fallback_when_text_search_empty():
    calls: list[dict] = []

    def fake_search(**kwargs):
        calls.append(dict(kwargs))
        if kwargs.get('query'):
            return {
                'destination': kwargs['destination'],
                'total': '0',
                'results': [],
                'error': None,
                'query': kwargs['query'],
                'meta': {'hint': 'zero_results_territory_wide'},
            }
        return {
            'destination': kwargs['destination'],
            'total': '2',
            'results': [
                {'title': 'Arena Tapas Restaurant', 'url': 'https://www.femturisme.cat/establiments/arena'},
                {'title': 'Cal Candi', 'url': 'https://www.femturisme.cat/establiments/cal-candi'},
            ],
            'error': None,
        }

    with patch(
        'app.services.tools.establishments.establishments.search',
        side_effect=fake_search,
    ):
        out = json.loads(execute({
            'destination': 'Catalunya',
            'type': 'restaurant',
            'query': 'macarrons',
        }))

    assert len(calls) == 2
    assert calls[1]['query'] is None
    assert out['total'] == '0'
    assert out['meta']['hint'] == 'zero_results_text_query'
    assert out['meta']['fallback_applied'] is True
    assert len(out['fallback_results']) == 2
