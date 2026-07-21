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


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_experiences_costa_brava_tourism_zone(app):
    """Costa Brava resolves to municipality IDs and returns promotional offers."""
    experiences = pytest.importorskip('app.db.repositories.experiences')
    with app.app_context():
        data = experiences.search(destination='Costa Brava')
    assert int(data['total']) >= 1
    meta = data.get('meta') or {}
    assert meta.get('resolved_zone') == 'Costa Brava'
    assert meta.get('resolved_comarques')
    assert data['results'][0]['url'].startswith('https://www.femturisme.cat/')


@pytest.mark.integration
@pytest.mark.skipif(not mysql_available(), reason='MYSQL_* not configured')
def test_experiences_calella_50km_guided_visits(app):
    """SQL-06b: Calella + 50 km + Visites guiades → radius meta and >=1 offer."""
    experiences = pytest.importorskip('app.db.repositories.experiences')
    geo_radius = pytest.importorskip('app.db.geo_radius')
    with app.app_context():
        origin = geo_radius.resolve_origin_coordinates('Calella')
        if origin is None:
            pytest.skip('Calella coordinates not available in staging MySQL')
        data = experiences.search(
            destination='Calella',
            category='Visites guiades',
            distance_km=50,
        )
    meta = data.get('meta') or {}
    if meta.get('scope') != 'radius':
        pytest.skip('Radius origin could not be resolved for Calella')
    assert meta['distance_km'] == 50
    assert meta['origin']['label']
    assert int(data['total']) >= 1
    assert data['results'][0]['url'].startswith('https://www.femturisme.cat/ofertes/')
