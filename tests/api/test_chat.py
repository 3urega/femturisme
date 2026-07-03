"""API tests — tecnic.md §14.2."""
from __future__ import annotations

from tests.helpers.sse import parse_sse_events


def test_api_01_chat_empty_message_returns_400(client):
    """API-01: POST /api/chat with empty message → 400."""
    response = client.post('/api/chat', json={'message': '   '})
    assert response.status_code == 400
    data = response.get_json()
    assert data is not None
    assert 'error' in data


def test_api_02_chat_simple_message_sse_done(client):
    """API-02: simple question → SSE stream contains done event."""
    response = client.post('/api/chat', json={'message': 'Hola'})
    assert response.status_code == 200
    assert 'text/event-stream' in response.content_type

    events = parse_sse_events(response.data)
    types = [e.get('type') for e in events]
    assert 'done' in types
    assert any(e.get('type') == 'text_chunk' for e in events)


def test_api_03_chat_catalog_tool_flow(client, mock_tool_execute):
    """API-03: catalog question → tool_call, tool_result, text_chunk, done."""
    response = client.post(
        '/api/chat',
        json={'message': 'Quines rutes hi ha al Berguedà?'},
    )
    assert response.status_code == 200

    events = parse_sse_events(response.data)
    types = [e.get('type') for e in events]

    assert 'tool_call' in types
    assert 'tool_result' in types
    assert 'text_chunk' in types
    assert 'done' in types

    tool_call_idx = types.index('tool_call')
    tool_result_idx = types.index('tool_result')
    done_idx = types.index('done')
    assert tool_call_idx < tool_result_idx < done_idx


def test_api_04_session_reset_ok(client):
    """API-04: POST /api/session/reset → ok true."""
    session_id = 'test-session-reset-001'

    client.post('/api/chat', json={
        'message': 'Hola',
        'session_id': session_id,
    })

    response = client.post('/api/session/reset', json={'session_id': session_id})
    assert response.status_code == 200
    assert response.get_json() == {'ok': True}
