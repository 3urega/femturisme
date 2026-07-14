"""SQL integration tests — search_establishments (tecnic SQL-01, SQL-02)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_establishments_girona_hotel(app):
    """SQL-01: destination=Girona, type=hotel → >=0 files, URL vàlida."""
    establishments = pytest.importorskip('app.db.repositories.establishments')
    with app.app_context():
        data = establishments.search(destination='Girona', type='hotel')
    assert int(data['total']) >= 0
    if int(data['total']) >= 1:
        assert data['results'][0]['url'].startswith('https://www.femturisme.cat/')


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_establishments_pals_restaurant(app):
    """SQL-02: destination=Pals, type=restaurant → >=0 menjar."""
    establishments = pytest.importorskip('app.db.repositories.establishments')
    with app.app_context():
        data = establishments.search(destination='Pals', type='restaurant')
    assert int(data['total']) >= 0


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_establishments_catalunya_restaurant_macarrons_query(app):
    """SQL-03: free-text query for dish keyword in establishment descriptions."""
    establishments = pytest.importorskip('app.db.repositories.establishments')
    with app.app_context():
        data = establishments.search(
            destination='Catalunya',
            type='restaurant',
            query='macarrons',
        )
    assert data.get('error') is None
    assert int(data['total']) >= 0
    for card in data['results']:
        assert card['url'].startswith('https://www.femturisme.cat/establiments/')


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_establishments_girona_location_filter_not_bypassed(app):
    """Regression: LIKE location filter must not return unrelated cities."""
    establishments = pytest.importorskip('app.db.repositories.establishments')
    with app.app_context():
        data = establishments.search(destination='Girona')
    if int(data['total']) >= 1:
        for card in data['results']:
            location = (card.get('location') or '').lower()
            assert 'barcelona' not in location


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_establishments_pirineu_casa_rural(app):
    """Pirineu tourism zone + rural type alias returns catalog results."""
    from app.services.tools.establishments import execute
    import json

    with app.app_context():
        data = json.loads(execute({
            'destination': 'Pirineu',
            'type': 'casa-rural',
        }))
    assert int(data['total']) >= 1
    meta = data.get('meta') or {}
    assert meta.get('resolved_zone') == 'Pirineu'
    assert data['results'][0]['url'].startswith('https://www.femturisme.cat/establiments/')
