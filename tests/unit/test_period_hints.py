"""Unit tests for app.services.period_hints."""
from __future__ import annotations

import json
from datetime import date

from app.services.period_hints import (
    apply_event_period_hints,
    build_forced_search_events_input,
    infer_event_period,
    is_agenda_search_query,
)


def test_infer_event_period_aquest_mes():
    period = infer_event_period(
        "Quins events i fires hi ha a Catalunya aquest mes?",
        today=date(2026, 7, 13),
    )
    assert period == ("2026-07-01", "2026-07-31")


def test_infer_event_period_cap_de_setmana():
    period = infer_event_period(
        "Què fer aquest cap de setmana a l'Empordà?",
        today=date(2026, 7, 13),  # Monday
    )
    assert period == ("2026-07-18", "2026-07-19")


def test_infer_event_period_named_month():
    period = infer_event_period(
        "Events a Barcelona el juliol",
        today=date(2026, 3, 1),
    )
    assert period == ("2026-07-01", "2026-07-31")


def test_infer_event_period_none_without_hint():
    assert infer_event_period("Events a Girona", today=date(2026, 7, 13)) is None


def test_apply_event_period_hints_overrides_wrong_llm_dates():
    merged = apply_event_period_hints(
        'search_events',
        {
            'destination': 'Catalunya',
            'date_from': '2024-06-01',
            'date_to': '2024-06-30',
        },
        "Quins events i fires hi ha a Catalunya aquest mes?",
        today=date(2026, 7, 13),
    )
    assert merged['date_from'] == '2026-07-01'
    assert merged['date_to'] == '2026-07-31'
    assert merged['_period_hint_applied'] is True


def test_correct_stale_dates_when_relative_marker_without_aquest_mes():
    merged = apply_event_period_hints(
        'search_events',
        {
            'destination': 'Catalunya',
            'date_from': '2024-06-01',
            'date_to': '2024-06-30',
        },
        "Quins events hi ha aquest juliol a Catalunya?",
        today=date(2026, 7, 13),
    )
    assert merged['date_from'] == '2026-07-01'
    assert merged['date_to'] == '2026-07-31'



def test_sanitize_hallucinated_year_drops_dates_without_month_hint():
    merged = apply_event_period_hints(
        'search_events',
        {
            'destination': 'Girona',
            'date_from': '2024-06-01',
            'date_to': '2024-06-30',
        },
        'Quins events hi ha a Girona?',
        today=date(2026, 7, 13),
    )
    assert 'date_from' not in merged
    assert 'date_to' not in merged
    assert merged.get('_stale_dates_removed') is True


def test_execute_tool_uses_context_user_message(monkeypatch):
    from app.services.request_context import turn_user_message
    from app.services.tools import execute_tool

    captured: list[dict] = []

    def fake_events(tool_input: dict) -> str:
        captured.append(dict(tool_input))
        return json.dumps({'destination': 'Catalunya', 'total': '1', 'results': [], 'error': None})

    monkeypatch.setitem(
        __import__('app.services.tools', fromlist=['_EXECUTORS'])._EXECUTORS,
        'search_events',
        fake_events,
    )
    token = turn_user_message.set('Quins events i fires hi ha a Catalunya aquest mes?')
    try:
        execute_tool('search_events', {
            'destination': 'Catalunya',
            'date_from': '2024-06-01',
            'date_to': '2024-06-30',
        })
    finally:
        turn_user_message.reset(token)

    assert captured[0]['date_from'] == '2026-07-01'
    assert captured[0]['date_to'] == '2026-07-31'


def test_execute_tool_accepts_explicit_user_message(monkeypatch):
    from app.services.tools import execute_tool

    captured: list[dict] = []

    def fake_events(tool_input: dict) -> str:
        captured.append(dict(tool_input))
        return json.dumps({'destination': 'Catalunya', 'total': '1', 'results': [], 'error': None})

    monkeypatch.setitem(
        __import__('app.services.tools', fromlist=['_EXECUTORS'])._EXECUTORS,
        'search_events',
        fake_events,
    )
    execute_tool(
        'search_events',
        {
            'destination': 'Catalunya',
            'date_from': '2024-06-01',
            'date_to': '2024-06-30',
        },
        user_message='Quins events i fires hi ha a Catalunya aquest mes?',
    )
    assert captured[0]['date_from'] == '2026-07-01'


def test_apply_event_period_hints_ignores_other_tools():
    original = {'destination': 'Girona'}
    assert apply_event_period_hints(
        'search_routes',
        original,
        "Quins events aquest mes?",
        today=date(2026, 7, 13),
    ) == original


def test_is_agenda_search_query_catalunya_aquest_mes():
    message = "Quins events i fires hi ha a Catalunya aquest mes?"
    assert is_agenda_search_query(message) is True


def test_is_agenda_search_query_meta_question_false():
    assert is_agenda_search_query("Què són les fires de Catalunya?") is False


def test_build_forced_search_events_input_catalunya():
    forced = build_forced_search_events_input(
        "Quins events i fires hi ha a Catalunya aquest mes?",
        today=date(2026, 7, 13),
    )
    assert forced is not None
    assert forced['destination'] == 'Catalunya'
    assert forced['date_from'] == '2026-07-01'
    assert forced['date_to'] == '2026-07-31'
