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
