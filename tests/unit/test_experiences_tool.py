"""Unit tests — search_experiences tool."""
from __future__ import annotations

from app.services.tools.experiences import _normalize_category


def test_normalize_category_maps_aliases():
    assert _normalize_category('activitats') == 'Activitats'
    assert _normalize_category('Familiar') == 'Familiar'


def test_normalize_category_drops_invalid_natura():
    assert _normalize_category('Natura') is None
    assert _normalize_category('senderisme') is None
