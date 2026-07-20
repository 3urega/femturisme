"""Unit tests for search_events tool — issue #36."""
from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import patch

from app.services.tools import events as events_tool


def test_execute_requires_destination_or_query():
    out = json.loads(events_tool.execute({}))
    assert 'At least one of destination or query is required' in out['error']


def test_execute_query_only_uses_twelve_month_window():
    today = date(2026, 7, 15)
    captured: dict = {}

    def _fake_search(**kwargs):
        captured.update(kwargs)
        return {
            'destination': '',
            'total': '0',
            'results': [],
            'error': None,
            'query': kwargs.get('query'),
        }

    with patch.object(events_tool.events, 'search', side_effect=_fake_search):
        with patch('app.services.tools.events.date') as mock_date:
            mock_date.today.return_value = today
            out = json.loads(events_tool.execute({'query': 'patum'}))

    assert out.get('error') is None
    assert captured['query'] == 'patum'
    assert captured['destination'] is None
    assert captured['date_from'] == today.isoformat()
    assert captured['date_to'] == (today + timedelta(days=365)).isoformat()


def test_execute_destination_only_uses_current_month():
    today = date(2026, 7, 15)
    captured: dict = {}

    def _fake_search(**kwargs):
        captured.update(kwargs)
        return {
            'destination': 'Girona',
            'total': '0',
            'results': [],
            'error': None,
        }

    with patch.object(events_tool.events, 'search', side_effect=_fake_search):
        with patch('app.services.tools.events.date') as mock_date:
            mock_date.today.return_value = today
            json.loads(events_tool.execute({'destination': 'Girona'}))

    assert captured['destination'] == 'Girona'
    assert captured['date_from'] == '2026-07-01'
    assert captured['date_to'] == '2026-07-31'


def test_schema_includes_query_and_optional_destination():
    props = events_tool.SCHEMA['input_schema']['properties']
    assert 'query' in props
    assert events_tool.SCHEMA['input_schema']['required'] == []
