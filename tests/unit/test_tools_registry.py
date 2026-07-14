"""Unit tests for catalog tool registry — issue #15 / DEV-307."""
from __future__ import annotations

import json

from app.services.request_context import turn_user_language
from app.services.tools import ALL_TOOLS, CATALOG_TOOLS, CATALOG_TOOL_NAMES, _EXECUTORS, execute_tool

CATALOG_TOOL_NAMES_SET = frozenset({
    'search_establishments',
    'search_destinations',
    'search_events',
    'search_articles',
    'search_experiences',
    'search_routes',
})

AUX_TOOL_NAMES = frozenset({'search_local_knowledge'})

EXPECTED_TOOL_NAMES = CATALOG_TOOL_NAMES_SET | AUX_TOOL_NAMES


def test_catalog_tools_lists_six_mysql_searchers():
    names = {schema['name'] for schema in CATALOG_TOOLS}
    assert names == CATALOG_TOOL_NAMES_SET
    assert len(CATALOG_TOOLS) == 6


def test_femturisme_llm_tools_exclude_auxiliary_knowledge():
    names = {schema['name'] for schema in CATALOG_TOOLS}
    assert 'search_local_knowledge' not in names
    assert 'search_entity_knowledge' not in names


def test_all_tools_lists_six_catalog_plus_local_knowledge():
    names = {schema['name'] for schema in ALL_TOOLS}
    assert names == EXPECTED_TOOL_NAMES
    assert len(ALL_TOOLS) == 7


def test_executors_cover_all_registered_tools():
    assert set(_EXECUTORS.keys()) == EXPECTED_TOOL_NAMES


def test_no_legacy_search_accommodations():
    names = {schema['name'] for schema in ALL_TOOLS}
    assert 'search_accommodations' not in names


def test_execute_tool_unknown_returns_error():
    out = json.loads(execute_tool('search_nonexistent', {}))
    assert 'error' in out
    assert 'Unknown tool' in out['error']


def test_execute_tool_resolves_catalog_tools_without_unknown_error():
    """Each catalog tool is registered; missing required args return validation, not Unknown tool."""
    cases = {
        'search_establishments': {'destination': '', 'query': ''},
        'search_destinations': {'destination': ''},
        'search_events': {'destination': ''},
        'search_articles': {},
        'search_experiences': {'destination': ''},
        'search_routes': {'destination': ''},
        'search_local_knowledge': {'query': 'test'},
    }
    for name, tool_input in cases.items():
        out = json.loads(execute_tool(name, tool_input))
        assert 'Unknown tool' not in str(out.get('error', ''))


def test_execute_tool_injects_lang_from_context(monkeypatch):
    import app.services.tools as tools_mod

    turn_user_language.set('es')
    captured: dict = {}

    def _fake_routes(tool_input: dict) -> str:
        captured.update(tool_input)
        return json.dumps({'total': '0', 'results': []})

    monkeypatch.setattr(
        tools_mod,
        '_EXECUTORS',
        {**tools_mod._EXECUTORS, 'search_routes': _fake_routes},
    )
    execute_tool('search_routes', {'destination': 'Girona'})
    assert captured.get('lang') == 'es'
