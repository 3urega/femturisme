"""SQL integration tests — search_experiences (tecnic SQL-06)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_experiences_olvan(app):
    """SQL-06: destination=Olvan → >=0 experiències promocionals."""
    experiences = pytest.importorskip('app.db.repositories.experiences')
    with app.app_context():
        data = experiences.search(destination='Olvan')
    assert int(data['total']) >= 0
    if int(data['total']) >= 1:
        assert data['results'][0]['title']
        assert data['results'][0]['url'].startswith('https://www.femturisme.cat/')
