"""SQL integration tests — search_destinations (tecnic SQL-04)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_destinations_besalu(app):
    """SQL-04: destination=Besalú → >=0 poblacions/on anar."""
    destinations = pytest.importorskip('app.db.repositories.destinations')
    with app.app_context():
        data = destinations.search(destination='Besalú')
    assert int(data['total']) >= 0
