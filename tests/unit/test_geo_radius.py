"""Unit tests for app.db.geo_radius."""
from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.db.geo_radius import (
    OriginPoint,
    build_radius_filter,
    haversine_km_predicate,
    resolve_origin_coordinates,
)


def test_haversine_km_predicate_returns_four_placeholders_and_ordered_params():
    clause, params = haversine_km_predicate(
        lat_expr='CAST(eg.latitud AS DECIMAL(10,6))',
        lng_expr='CAST(eg.longitud AS DECIMAL(10,6))',
        origin_lat=41.613,
        origin_lng=2.653,
        max_km=50.0,
    )

    assert clause.count('%s') == 4
    assert params == [41.613, 2.653, 41.613, 50.0]
    assert '6371' in clause
    assert 'ACOS' in clause
    assert 'CAST(eg.latitud AS DECIMAL(10,6))' in clause


def test_haversine_km_predicate_rejects_non_positive_radius():
    clause, params = haversine_km_predicate(
        lat_expr='pg.latitud',
        lng_expr='pg.longitud',
        origin_lat=41.0,
        origin_lng=2.0,
        max_km=0,
    )
    assert clause == '(%s IS NULL)'
    assert params == [None]


def test_build_radius_filter_delegates_to_haversine():
    origin = OriginPoint(lat=41.613, lng=2.653, label='Calella', source='poble_general')
    clause, params = build_radius_filter(
        origin,
        lat_expr='pg.latitud',
        lng_expr='pg.longitud',
        max_km=25,
    )
    assert params[-1] == 25
    assert 'pg.latitud' in clause


@contextmanager
def _mock_mysql_fetch(row):
    cursor = MagicMock()
    cursor.fetchone.return_value = row
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False
    with patch('app.db.geo_radius.get_mysql_connection', return_value=conn):
        yield cursor


def test_resolve_origin_coordinates_from_poble_general():
    row = {'latitud': '41.613', 'longitud': '2.653', 'poble': 'Calella'}
    with _mock_mysql_fetch(row):
        origin = resolve_origin_coordinates('Calella')

    assert origin == OriginPoint(
        lat=41.613,
        lng=2.653,
        label='Calella',
        source='poble_general',
    )


def test_resolve_origin_coordinates_falls_back_to_generic_ubicacions():
    generic_row = {
        'latitud': '42.1',
        'longitud': '2.5',
        'ubicacio': 'Alt Empordà',
    }
    with _mock_mysql_fetch(None) as cursor:
        cursor.fetchone.side_effect = [None, generic_row]
        origin = resolve_origin_coordinates('Alt Empordà')

    assert origin == OriginPoint(
        lat=42.1,
        lng=2.5,
        label='Alt Empordà',
        source='generic_ubicacions',
    )


def test_resolve_origin_coordinates_broad_territory_returns_none():
    assert resolve_origin_coordinates('Catalunya') is None
    assert resolve_origin_coordinates('') is None


@pytest.mark.parametrize(
    'row',
    [
        {'latitud': '', 'longitud': '2.653', 'poble': 'Calella'},
        {'latitud': '0', 'longitud': '2.653', 'poble': 'Calella'},
        {'latitud': '91', 'longitud': '2.653', 'poble': 'Calella'},
        {'latitud': '41.613', 'longitud': '200', 'poble': 'Calella'},
    ],
)
def test_resolve_origin_coordinates_invalid_coords_return_none(row):
    with _mock_mysql_fetch(row):
        assert resolve_origin_coordinates('Calella') is None
