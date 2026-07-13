"""Unit tests for catalog tool registry — issue #15 / DEV-307."""
from __future__ import annotations

import json

from app.services.tools import ALL_TOOLS, _EXECUTORS, execute_tool

CATALOG_TOOL_NAMES = frozenset({
    'search_establishments',
    'search_destinations',
    'search_events',
    'search_articles',
    'search_experiences',
    'search_routes',
})

AUX_TOOL_NAMES = frozenset({'search_local_knowledge'})

EXPECTED_TOOL_NAMES = CATALOG_TOOL_NAMES | AUX_TOOL_NAMES


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
        'search_establishments': {'destination': ''},
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
