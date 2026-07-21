"""Unit tests — search_experiences tool and repository."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.db.geo_radius import OriginPoint
from app.db.repositories import experiences as experiences_repo
from app.services.tools.experiences import (
    _normalize_category,
    _parse_distance_km,
    execute,
)


def test_normalize_category_maps_aliases():
    assert _normalize_category('activitats') == 'Activitats'
    assert _normalize_category('Familiar') == 'Familiar'


def test_normalize_category_drops_invalid_natura():
    assert _normalize_category('Natura') is None
    assert _normalize_category('senderisme') is None


def test_parse_distance_km_valid():
    assert _parse_distance_km(50) == 50.0
    assert _parse_distance_km('25') == 25.0


def test_parse_distance_km_clamps_to_max():
    assert _parse_distance_km(150) == 100.0


def test_parse_distance_km_rejects_invalid():
    assert _parse_distance_km(None) is None
    assert _parse_distance_km(0) is None
    assert _parse_distance_km(-5) is None
    assert _parse_distance_km('abc') is None


def test_execute_passes_distance_km_to_repository():
    payload = {
        'destination': 'Calella',
        'category': 'Visites guiades',
        'distance_km': 50,
    }
    with patch('app.services.tools.experiences.experiences.search') as mock_search:
        mock_search.return_value = {
            'destination': 'Calella',
            'total': '1',
            'results': [{'title': 'Test', 'url': 'https://www.femturisme.cat/ofertes/x'}],
            'error': None,
        }
        result = json.loads(execute(payload))

    mock_search.assert_called_once_with(
        destination='Calella',
        category='Visites guiades',
        establishment=None,
        lang='ca',
        distance_km=50.0,
        skip_location_filter=False,
        retried=False,
    )
    assert result['total'] == '1'


def test_search_radius_mode_uses_haversine_and_radius_meta():
    origin = OriginPoint(
        lat=41.613,
        lng=2.653,
        label='Calella',
        source='poble_general',
    )
    fake_row = {
        'id': 1,
        'title': 'Visita guiada',
        'param_url': 'visita-test',
        'description': 'Desc',
        'image': None,
        'preu_oferta': None,
        'establishment_name': 'Hotel',
        'location': 'Barcelona',
        'comarca': 'Barcelonès',
        'category': 'Visites guiades',
    }
    cursor = MagicMock()
    cursor.fetchall.return_value = [fake_row]
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False

    with patch('app.db.repositories.experiences.get_mysql_connection', return_value=conn):
        with patch(
            'app.db.repositories.experiences.resolve_origin_coordinates',
            return_value=origin,
        ) as mock_resolve:
            with patch(
                'app.db.repositories.experiences.build_radius_filter',
                return_value=('(haversine_clause)', [41.613, 2.653, 41.613, 50.0]),
            ) as mock_radius:
                data = experiences_repo.search(
                    destination='Calella',
                    category='Visites guiades',
                    distance_km=50,
                )

    mock_resolve.assert_called_once()
    mock_radius.assert_called_once()
    executed_sql = cursor.execute.call_args[0][0]
    assert 'haversine_clause' in executed_sql
    assert data['meta']['scope'] == 'radius'
    assert data['meta']['distance_km'] == 50
    assert data['meta']['origin']['label'] == 'Calella'


def test_search_radius_without_origin_falls_back_with_hint():
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False

    with patch('app.db.repositories.experiences.get_mysql_connection', return_value=conn):
        with patch(
            'app.db.repositories.experiences.resolve_origin_coordinates',
            return_value=None,
        ):
            data = experiences_repo.search(destination='UnknownPlace', distance_km=50)

    assert data['meta']['hint'] == 'radius_origin_unresolved'
    assert data['meta']['distance_km'] == 50
    assert data['meta']['scope'] == 'location'
