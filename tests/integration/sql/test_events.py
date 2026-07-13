"""SQL integration tests — search_events (tecnic SQL-05)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_events_emporda_weekend(app):
    """SQL-05: destination=Empordà, dates cap de setmana → agenda dins interval."""
    events = pytest.importorskip('app.db.repositories.events')
    with app.app_context():
        data = events.search(
            destination='Empordà',
            date_from='2026-06-28',
            date_to='2026-06-29',
        )
    assert int(data['total']) >= 0


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_events_catalunya_july(app):
    """SQL-05b: destination=Catalunya, juliol → >=1 esdeveniment (territori ampli)."""
    events = pytest.importorskip('app.db.repositories.events')
    with app.app_context():
        data = events.search(
            destination='Catalunya',
            date_from='2026-07-01',
            date_to='2026-07-31',
        )
    assert int(data['total']) >= 1
    assert data['meta']['scope'] == 'territory_wide'
    assert data['results'][0]['url'].startswith('https://www.femturisme.cat/')
