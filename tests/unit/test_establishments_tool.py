"""Unit tests for search_establishments tool."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.db.geo_radius import OriginPoint
from app.db.repositories import establishments as establishments_repo
from app.services.tools.establishments import (
    SCHEMA,
    _normalize_type,
    _parse_distance_km,
    execute,
)


def test_schema_includes_query_parameter():
    props = SCHEMA['input_schema']['properties']
    assert 'query' in props
    assert 'distance_km' in props
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


def test_normalize_type_maps_casa_rural_to_cases_rurals():
    assert _normalize_type('casa-rural') == 'cases-rurals'
    assert _normalize_type('turisme rural') == 'cases-rurals'
    assert _normalize_type('hotel') == 'hotel'


def test_execute_normalizes_casa_rural_type():
    captured: dict = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return {'destination': kwargs['destination'], 'total': '1', 'results': [], 'error': None}

    with patch(
        'app.services.tools.establishments.establishments.search',
        side_effect=fake_search,
    ):
        execute({'destination': 'Pirineu', 'type': 'casa-rural'})

    assert captured['type'] == 'cases-rurals'


def test_parse_distance_km_valid():
    assert _parse_distance_km(30) == 30.0
    assert _parse_distance_km('25') == 25.0


def test_parse_distance_km_clamps_to_max():
    assert _parse_distance_km(150) == 100.0


def test_parse_distance_km_rejects_invalid():
    assert _parse_distance_km(None) is None
    assert _parse_distance_km(0) is None
    assert _parse_distance_km(-5) is None
    assert _parse_distance_km('abc') is None


def test_execute_passes_distance_km_to_repository():
    captured: dict = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return {
            'destination': kwargs['destination'],
            'total': '1',
            'results': [{'title': 'Hotel', 'url': 'https://example.com'}],
            'error': None,
        }

    with patch(
        'app.services.tools.establishments.establishments.search',
        side_effect=fake_search,
    ):
        execute({'destination': 'Berga', 'distance_km': 30})

    assert captured['destination'] == 'Berga'
    assert captured['distance_km'] == 30.0


def test_search_radius_mode_uses_haversine_and_radius_meta():
    origin = OriginPoint(
        lat=42.104,
        lng=1.846,
        label='Berga',
        source='poble_general',
    )
    fake_row = {
        'id': 1,
        'title': 'Hotel Estel',
        'param_url': 'hotel-estel',
        'image': None,
        'type_code': 'hotels',
        'type_label': 'Hotels',
        'location': 'Berga',
        'comarca': 'Berguedà',
        'description': 'Desc',
    }
    cursor = MagicMock()
    cursor.fetchall.return_value = [fake_row]
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False

    with patch('app.db.repositories.establishments.get_mysql_connection', return_value=conn):
        with patch(
            'app.db.repositories.establishments.resolve_origin_coordinates',
            return_value=origin,
        ) as mock_resolve:
            with patch(
                'app.db.repositories.establishments.build_radius_filter',
                return_value=('(haversine_clause)', [42.104, 1.846, 42.104, 30.0]),
            ) as mock_radius:
                data = establishments_repo.search(
                    destination='Berga',
                    distance_km=30,
                )

    mock_resolve.assert_called_once()
    mock_radius.assert_called_once()
    executed_sql = cursor.execute.call_args[0][0]
    assert 'haversine_clause' in executed_sql
    assert data['meta']['scope'] == 'radius'
    assert data['meta']['distance_km'] == 30
    assert data['meta']['origin']['label'] == 'Berga'


def test_search_radius_without_origin_falls_back_with_hint():
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False

    with patch('app.db.repositories.establishments.get_mysql_connection', return_value=conn):
        with patch(
            'app.db.repositories.establishments.resolve_origin_coordinates',
            return_value=None,
        ):
            data = establishments_repo.search(destination='UnknownPlace', distance_km=30)

    assert data['meta']['hint'] == 'radius_origin_unresolved'
    assert data['meta']['distance_km'] == 30
    assert data['meta']['scope'] == 'location'
