"""
Tool registry — add new tools here.

Each tool module exposes:
  SCHEMA  : dict  — JSON schema in Anthropic format (name, description, input_schema)
  execute : callable(input: dict) -> str (JSON string)
"""
from __future__ import annotations

import json

from app.db.territory import is_broad_territory
from app.services.period_hints import apply_event_period_hints
from app.services.request_context import turn_user_message

from .establishments   import SCHEMA as EST_SCHEMA, execute as est_execute
from .destinations     import SCHEMA as DST_SCHEMA, execute as dst_execute
from .events           import SCHEMA as EVT_SCHEMA, execute as evt_execute
from .articles         import SCHEMA as ART_SCHEMA, execute as art_execute
from .experiences      import SCHEMA as EXP_SCHEMA, execute as exp_execute
from .routes_tool      import SCHEMA as RTE_SCHEMA, execute as rte_execute
from .local_knowledge  import SCHEMA as LOC_SCHEMA, execute as loc_execute

# Ordered list used by the agent
ALL_TOOLS: list[dict] = [
    EST_SCHEMA,
    DST_SCHEMA,
    EVT_SCHEMA,
    ART_SCHEMA,
    EXP_SCHEMA,
    RTE_SCHEMA,
    LOC_SCHEMA,
]

_EXECUTORS: dict[str, callable] = {
    EST_SCHEMA['name']: est_execute,
    DST_SCHEMA['name']: dst_execute,
    EVT_SCHEMA['name']: evt_execute,
    ART_SCHEMA['name']: art_execute,
    EXP_SCHEMA['name']: exp_execute,
    RTE_SCHEMA['name']: rte_execute,
    LOC_SCHEMA['name']: loc_execute,
}

_GEO_CATALOG_TOOLS = frozenset({
    'search_events',
    'search_routes',
    'search_experiences',
    'search_establishments',
    'search_destinations',
})


def _parse_tool_result(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _should_retry_broad_territory(
    name: str,
    tool_input: dict,
    parsed: dict,
) -> bool:
    if name not in _GEO_CATALOG_TOOLS:
        return False
    if tool_input.get('_skip_location_filter'):
        return False
    if parsed.get('error'):
        return False
    try:
        total = int(parsed.get('total', 0) or 0)
    except (TypeError, ValueError):
        total = 0
    if total > 0:
        return False
    destination = (tool_input.get('destination') or '').strip()
    return is_broad_territory(destination)


def execute_tool(name: str, tool_input: dict, *, user_message: str = '') -> str:
    fn = _EXECUTORS.get(name)
    if fn is None:
        return json.dumps({'error': f'Unknown tool: {name}'})
    resolved_message = user_message or turn_user_message.get()
    normalized_input = apply_event_period_hints(
        name,
        tool_input,
        resolved_message,
    )
    raw_result = fn(normalized_input)
    parsed = _parse_tool_result(raw_result)
    if _should_retry_broad_territory(name, normalized_input, parsed):
        retry_input = {
            **normalized_input,
            '_skip_location_filter': True,
            '_retried': True,
        }
        raw_result = fn(retry_input)
    return raw_result
