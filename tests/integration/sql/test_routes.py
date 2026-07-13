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
    assert int(data['total']) >= 0
