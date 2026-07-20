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


def test_api_chat_accepts_optional_context(client, mock_tool_execute):
    """POST /api/chat with page_context and agent_context → 200 SSE done."""
    response = client.post(
        '/api/chat',
        json={
            'message': 'Què fer aquí?',
            'session_id': 'ctx-session-001',
            'page_context': {
                'section': 'agenda',
                'ubicacio': 'Empordà',
                'municipality': 'Pals',
            },
            'agent_context': {
                'mode': 'femturisme',
                'entity_id': None,
            },
        },
    )
    assert response.status_code == 200
    events = parse_sse_events(response.data)
    assert 'done' in [e.get('type') for e in events]


def test_api_chat_entitat_without_entity_id_400(client):
    response = client.post(
        '/api/chat',
        json={
            'message': 'Hola',
            'agent_context': {'mode': 'entitat'},
        },
    )
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_api_chat_entitat_with_entity_id_501(client):
    response = client.post(
        '/api/chat',
        json={
            'message': 'Hola',
            'agent_context': {
                'mode': 'entitat',
                'entity_id': '550e8400-e29b-41d4-a716-446655440000',
            },
        },
    )
    assert response.status_code == 501
    assert 'error' in response.get_json()


def test_api_multi_turn_same_session_preserves_context(client, mock_tool_execute):
    """Multi-turn: same session_id accumulates history; turn 2 triggers catalog tool."""
    from app.services import agent_service

    session_id = 'multi-turn-ctx-001'

    r1 = client.post('/api/chat', json={
        'message': 'Vull anar al Berguedà aquest cap de setmana.',
        'session_id': session_id,
    })
    assert r1.status_code == 200
    assert 'done' in [e.get('type') for e in parse_sse_events(r1.data)]

    history_after_t1 = list(agent_service._history.get(session_id, []))
    assert len(history_after_t1) >= 2

    r2 = client.post('/api/chat', json={
        'message': 'On puc dormir allà?',
        'session_id': session_id,
    })
    assert r2.status_code == 200
    events2 = parse_sse_events(r2.data)
    types2 = [e.get('type') for e in events2]
    assert 'done' in types2
    assert 'tool_call' in types2
    tool_calls = [e for e in events2 if e.get('type') == 'tool_call']
    assert any(e.get('tool') == 'search_establishments' for e in tool_calls)

    history_after_t2 = agent_service._history.get(session_id, [])
    assert len(history_after_t2) > len(history_after_t1)
    first_user = history_after_t2[0].get('content', '')
    assert 'bergued' in str(first_user).lower()


def test_api_05_chat_rate_limit_returns_429(client, app):
    """Rate limit: excess POST /api/chat → 429 JSON."""
    from app.services.rate_limit import reset

    reset()
    app.config['RATE_LIMIT_PER_IP'] = 2
    app.config['RATE_LIMIT_PER_SESSION'] = 99
    session_id = 'rate-limit-test-session'

    assert client.post(
        '/api/chat',
        json={'message': 'Hola', 'session_id': session_id},
    ).status_code == 200
    assert client.post(
        '/api/chat',
        json={'message': 'Hola 2', 'session_id': session_id},
    ).status_code == 200

    response = client.post(
        '/api/chat',
        json={'message': 'Hola 3', 'session_id': session_id},
    )
    assert response.status_code == 429
    assert response.get_json()['error'] == 'rate limit exceeded'


def test_forced_keyword_patum(client, capture_tool_calls, llm_end_turn):
    """Issue #37: thematic query forces articles + events with query=patum."""
    response = client.post(
        '/api/chat',
        json={'message': 'Què és la Patum?', 'session_id': 'forced-kw-patum'},
    )
    assert response.status_code == 200
    events = parse_sse_events(response.data)
    types = [e.get('type') for e in events]
    assert 'tool_call' in types
    assert 'done' in types

    tool_names = [name for name, _ in capture_tool_calls]
    assert 'search_articles' in tool_names
    assert 'search_events' in tool_names
    for name, tool_input in capture_tool_calls:
        assert tool_input.get('query') == 'patum'


def test_forced_keyword_castellers(client, capture_tool_calls, llm_end_turn):
    """Issue #37: articles about castellers → search_articles with keyword."""
    response = client.post(
        '/api/chat',
        json={
            'message': 'Articles sobre castellers a Barcelona',
            'session_id': 'forced-kw-castellers',
        },
    )
    assert response.status_code == 200
    assert 'done' in [e.get('type') for e in parse_sse_events(response.data)]

    articles_calls = [
        inp for name, inp in capture_tool_calls if name == 'search_articles'
    ]
    assert articles_calls
    assert articles_calls[0].get('query') == 'castellers'
    assert articles_calls[0].get('destination') == 'Barcelona'


def test_forced_keyword_fira_medieval(client, capture_tool_calls, llm_end_turn):
    """Issue #37: when agenda force does not apply, fan-out with event query."""
    response = client.post(
        '/api/chat',
        json={
            'message': 'Quan és la Fira medieval de Pals?',
            'session_id': 'forced-kw-fira',
        },
    )
    assert response.status_code == 200
    assert 'done' in [e.get('type') for e in parse_sse_events(response.data)]

    events_calls = [
        inp for name, inp in capture_tool_calls if name == 'search_events'
    ]
    assert events_calls
    query = events_calls[0].get('query', '')
    assert 'fira' in query
    assert 'medieval' in query
