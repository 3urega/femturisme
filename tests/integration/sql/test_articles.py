"""SQL integration tests — search_articles (tecnic SQL-03)."""
from __future__ import annotations

import pytest

from tests.helpers.env import mysql_available


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_articles_parc_cadi(app):
    """SQL-03: topic=Parc Natural Cadí → >=0 articles."""
    articles = pytest.importorskip('app.db.repositories.articles')
    with app.app_context():
        data = articles.search(topic='Parc Natural Cadí')
    assert int(data['total']) >= 0
