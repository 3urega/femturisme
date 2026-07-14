"""Unit tests for structured request logging."""
from __future__ import annotations

import json
import logging

import pytest

from app.services.request_logging import (
    log_catalog_query,
    log_chat_turn,
    log_error,
    safe_tool_params,
)


@pytest.fixture
def cap_agent_request(caplog):
    with caplog.at_level(logging.INFO, logger='agent.request'):
        yield caplog


def test_safe_tool_params_whitelist():
    params = safe_tool_params({
        'destination': 'Girona',
        'lang': 'ca',
        '_skip_location_filter': True,
        'user_secret': 'x',
    })
    assert params == {'destination': 'Girona', 'lang': 'ca'}


def test_log_chat_turn_emits_json(cap_agent_request, app):
    with app.app_context():
        log_chat_turn(
            session_id='sess-1',
            duration_ms=123.456,
            language='ca',
            operational_mode='femturisme',
            entity_id=None,
        )
    assert len(cap_agent_request.records) == 1
    payload = json.loads(cap_agent_request.records[0].message)
    assert payload['event'] == 'chat_turn'
    assert payload['session_id'] == 'sess-1'
    assert payload['language'] == 'ca'
    assert payload['duration_ms'] == 123.46


def test_log_catalog_query_emits_json(cap_agent_request, app):
    with app.app_context():
        log_catalog_query(
            tool='search_routes',
            params={'destination': 'Empordà', 'lang': 'ca'},
            duration_ms=45.2,
            total='3',
        )
    payload = json.loads(cap_agent_request.records[0].message)
    assert payload['event'] == 'catalog_query'
    assert payload['tool'] == 'search_routes'
    assert payload['total'] == '3'


def test_log_error_without_exception(cap_agent_request, app):
    with app.app_context():
        log_error(session_id='sess-2', message='boom', error_code='E001')
    payload = json.loads(cap_agent_request.records[0].message)
    assert payload['event'] == 'error'
    assert payload['message'] == 'boom'


def test_log_error_with_exception(cap_agent_request, app):
    with app.app_context():
        try:
            raise ValueError('fail')
        except ValueError as exc:
            log_error(session_id='sess-3', message='wrapped', exc=exc)
    assert cap_agent_request.records[0].levelname == 'ERROR'


def test_logging_disabled_when_config_false(cap_agent_request, app):
    app.config['REQUEST_LOGGING_ENABLED'] = False
    with app.app_context():
        log_chat_turn(
            session_id='sess-off',
            duration_ms=1,
            language='ca',
            operational_mode='femturisme',
        )
    assert cap_agent_request.records == []


def test_execute_tool_logs_catalog_query(cap_agent_request, app, monkeypatch):
    import json

    import app.services.tools as tools_mod

    def _fake_routes(tool_input: dict) -> str:
        return json.dumps({'total': '2', 'results': []})

    monkeypatch.setattr(
        tools_mod,
        '_EXECUTORS',
        {**tools_mod._EXECUTORS, 'search_routes': _fake_routes},
    )
    with app.app_context():
        tools_mod.execute_tool('search_routes', {'destination': 'Girona'})
    payload = json.loads(cap_agent_request.records[0].message)
    assert payload['event'] == 'catalog_query'
    assert payload['tool'] == 'search_routes'
    assert payload['total'] == '2'
