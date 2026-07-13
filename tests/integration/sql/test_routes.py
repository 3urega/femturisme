"""SQL integration tests — search_routes (tecnic SQL-07)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_routes_emporda_foot(app):
    """SQL-07: destination=Empordà, type=A peu → >=1 ruta."""
    routes = pytest.importorskip('app.db.repositories.routes')
    with app.app_context():
        data = routes.search(destination='Empordà', type='A peu')
    assert int(data['total']) >= 1
    assert data['results'][0]['url'].startswith('https://www.femturisme.cat/')
    assert '/rutes/' in data['results'][0]['url']


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_routes_catalunya(app):
    """SQL-07b: destination=Catalunya → >=1 ruta (territori ampli)."""
    routes = pytest.importorskip('app.db.repositories.routes')
    with app.app_context():
        data = routes.search(destination='Catalunya')
    assert int(data['total']) >= 1
    assert data['meta']['scope'] == 'territory_wide'
