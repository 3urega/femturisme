"""Unit tests for reactive keyword fallback — issue #38."""
from __future__ import annotations

from app.services.query_keywords import build_keyword_fallback_calls


def test_fallback_after_empty_events_includes_articles_for_patum():
    executed = [('search_events', {'destination': 'Catalunya'})]
    calls = build_keyword_fallback_calls('Què és la Patum?', executed)
    assert calls is not None
    names = [name for name, _ in calls]
    assert 'search_articles' in names
    articles_input = next(inp for name, inp in calls if name == 'search_articles')
    assert articles_input['query'] == 'patum'
    assert articles_input['_keyword_fallback_applied'] is True


def test_fallback_skips_articles_when_already_queried():
    executed = [
        ('search_articles', {'query': 'patum'}),
        ('search_events', {'destination': 'Catalunya'}),
    ]
    calls = build_keyword_fallback_calls('Què és la Patum?', executed)
    assert calls is not None
    names = [name for name, _ in calls]
    assert 'search_articles' not in names
    assert 'search_events' in names


def test_fallback_returns_none_for_greeting():
    executed = [('search_events', {'destination': 'Catalunya'})]
    assert build_keyword_fallback_calls('Hola', executed) is None


def test_fallback_returns_none_when_already_applied():
    executed = [
        (
            'search_articles',
            {'query': 'patum', '_keyword_fallback_applied': True},
        ),
    ]
    assert build_keyword_fallback_calls('Què és la Patum?', executed) is None


def test_fallback_castellers_barcelona():
    executed = [('search_destinations', {'destination': 'Barcelona'})]
    calls = build_keyword_fallback_calls('Articles sobre castellers a Barcelona', executed)
    assert calls is not None
    articles_input = next(inp for name, inp in calls if name == 'search_articles')
    assert articles_input['query'] == 'castellers'
    assert articles_input.get('destination') == 'Barcelona'
