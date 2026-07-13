"""Unit tests for app.db.territory."""
from __future__ import annotations

from app.db.territory import (
    is_broad_territory,
    normalize_territory,
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
