"""Unit tests for SSE parsing helper."""
from __future__ import annotations

from tests.helpers.sse import parse_sse_events


def test_parse_sse_events_single():
    raw = 'data: {"type":"done","full_text":"Hola"}\n\n'
    events = parse_sse_events(raw)
    assert len(events) == 1
    assert events[0]['type'] == 'done'
    assert events[0]['full_text'] == 'Hola'


def test_parse_sse_events_multiple():
    raw = (
        'data: {"type":"tool_call","tool":"search_routes"}\n\n'
        'data: {"type":"tool_result","tool":"search_routes","result":{}}\n\n'
        'data: {"type":"done","full_text":"Fi"}\n\n'
    )
    events = parse_sse_events(raw)
    assert [e['type'] for e in events] == ['tool_call', 'tool_result', 'done']


def test_parse_sse_events_bytes():
    raw = b'data: {"type":"text_chunk","content":"Hola"}\n\n'
    events = parse_sse_events(raw)
    assert events[0]['content'] == 'Hola'


def test_parse_sse_events_ignores_empty_lines():
    raw = '\n\ndata: {"type":"done"}\n\n'
    events = parse_sse_events(raw)
    assert len(events) == 1
