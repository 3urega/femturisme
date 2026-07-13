"""Unit tests for broad-territory retry in execute_tool."""
from __future__ import annotations

import json
from unittest.mock import patch

from app.services.tools import execute_tool


def test_execute_tool_retries_broad_territory_when_zero_results():
    calls: list[dict] = []

    def fake_events(tool_input: dict) -> str:
        calls.append(dict(tool_input))
        if tool_input.get('_skip_location_filter'):
            return json.dumps({
                'destination': 'Catalunya',
                'total': '2',
                'results': [{'title': 'Event A'}],
                'error': None,
                'meta': {'scope': 'territory_wide', 'retried': True},
            })
        return json.dumps({
            'destination': 'Catalunya',
            'total': '0',
            'results': [],
            'error': None,
            'meta': {'scope': 'location', 'hint': 'zero_results_with_location'},
        })

    with patch.dict(
        'app.services.tools._EXECUTORS',
        {'search_events': fake_events},
    ):
        raw = execute_tool('search_events', {
            'destination': 'Catalunya',
            'date_from': '2026-07-01',
            'date_to': '2026-07-31',
        })

    parsed = json.loads(raw)
    assert parsed['total'] == '2'
    assert len(calls) == 2
    assert calls[1]['_skip_location_filter'] is True
    assert calls[1]['_retried'] is True


def test_execute_tool_no_retry_for_specific_destination():
    calls: list[dict] = []

    def fake_events(tool_input: dict) -> str:
        calls.append(dict(tool_input))
        return json.dumps({
            'destination': 'Girona',
            'total': '0',
            'results': [],
            'error': None,
            'meta': {'scope': 'location', 'hint': 'zero_results_with_location'},
        })

    with patch.dict(
        'app.services.tools._EXECUTORS',
        {'search_events': fake_events},
    ):
        raw = execute_tool('search_events', {'destination': 'Girona'})

    parsed = json.loads(raw)
    assert parsed['total'] == '0'
    assert len(calls) == 1


def test_execute_tool_no_retry_on_error():
    def fake_events(tool_input: dict) -> str:
        return json.dumps({
            'error': 'Database unavailable',
            'results': [],
        })

    with patch.dict(
        'app.services.tools._EXECUTORS',
        {'search_events': fake_events},
    ):
        raw = execute_tool('search_events', {'destination': 'Catalunya'})

    parsed = json.loads(raw)
    assert parsed['error'] == 'Database unavailable'
