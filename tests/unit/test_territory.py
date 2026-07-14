"""Unit tests for app.db.territory."""
from __future__ import annotations

from unittest.mock import patch

from app.db.territory import (
    GeoFilter,
    is_broad_territory,
    location_predicate,
    normalize_territory,
    resolve_geo_filter,
    resolve_location_filter,
)


def test_normalize_territory_strips_accents():
    assert normalize_territory('Cataluña') == 'cataluna'


def test_is_broad_territory_catalunya_variants():
    assert is_broad_territory('Catalunya')
    assert is_broad_territory('Cataluña')
    assert is_broad_territory('Catalonia')
    assert is_broad_territory('tot Catalunya')
    assert is_broad_territory('Andorra')


def test_is_broad_territory_specific_places():
    assert not is_broad_territory('Girona')
    assert not is_broad_territory('Empordà')
    assert not is_broad_territory('Barcelona')


def test_resolve_location_filter_broad():
    pattern, applied = resolve_location_filter('Catalunya')
    assert pattern is None
    assert applied is False


def test_resolve_location_filter_specific():
    pattern, applied = resolve_location_filter('Girona')
    assert pattern == '%Girona%'
    assert applied is True


def test_resolve_location_filter_skip_flag():
    pattern, applied = resolve_location_filter('Girona', skip_location_filter=True)
    assert pattern is None
    assert applied is False


def test_resolve_geo_filter_costa_brava_tourism_zone():
    fake_ids = tuple(range(1, 131))
    with patch(
        'app.db.territory._load_poble_ids_for_comarques',
        return_value=fake_ids,
    ):
        geo = resolve_geo_filter('Costa Brava')
    assert geo.kind == 'poble_ids'
    assert len(geo.poble_ids) == 130
    assert geo.resolved_zone == 'Costa Brava'
    assert geo.resolved_comarques == ('Alt Empordà', 'Baix Empordà', 'La Selva')
    assert geo.location_filter_applied is True
    assert geo.meta_extras()['resolved_zone'] == 'Costa Brava'


def test_resolve_geo_filter_girona_uses_like():
    geo = resolve_geo_filter('Girona')
    assert geo.kind == 'like'
    assert geo.pattern == '%Girona%'


def test_location_predicate_poble_ids_builds_in_clause():
    geo = GeoFilter(kind='poble_ids', poble_ids=(10, 20, 30), location_filter_applied=True)
    clause, params = location_predicate(geo)
    assert 'pg.id IN' in clause
    assert params[0] == 1
    assert params[1:] == [10, 20, 30]


def test_location_predicate_like_uses_non_null_guard():
    geo = GeoFilter(kind='like', pattern='%Girona%', location_filter_applied=True)
    clause, params = location_predicate(geo)
    assert params[0] == '%Girona%'
    assert params[0] is not None
    assert all(p == '%Girona%' for p in params)


def test_resolve_geo_filter_pirineu_tourism_zone():
    fake_ids = tuple(range(1, 226))
    with patch(
        'app.db.territory._load_poble_ids_for_comarques',
        return_value=fake_ids,
    ):
        geo = resolve_geo_filter('Pirineu')
    assert geo.kind == 'poble_ids'
    assert len(geo.poble_ids) == 225
    assert geo.resolved_zone == 'Pirineu'
    assert 'Berguedà' in geo.resolved_comarques
    assert geo.meta_extras()['resolved_zone'] == 'Pirineu'
