"""Unit tests for establishment domain hints — issue #52."""
from __future__ import annotations

from app.services.agent_service import AgentService
from app.services.domain_hints import (
    build_establishment_turn_instruction,
    infer_establishment_domain_context,
    is_establishment_domain_active,
    is_establishment_followup_message,
)
from app.services.query_keywords import (
    build_forced_keyword_tool_calls,
    build_keyword_fallback_calls,
    should_force_keyword_search,
)


def _patum_bergua_prior_history() -> list[dict]:
    return [
        {'role': 'user', 'content': 'Què en saps de la Patum?'},
        {
            'role': 'assistant',
            'content': [
                {
                    'type': 'tool_use',
                    'id': 't1',
                    'name': 'search_articles',
                    'input': {'query': 'patum'},
                },
                {
                    'type': 'tool_use',
                    'id': 't2',
                    'name': 'search_events',
                    'input': {'query': 'patum'},
                },
            ],
        },
        {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 't1', 'content': '{}'}]},
        {
            'role': 'assistant',
            'content': 'La Patum de Berga és una festa tradicional...',
        },
        {'role': 'user', 'content': 'buscam allotjament a prop de Berga'},
        {
            'role': 'assistant',
            'content': 'A quants km com a màxim vols que busqui des de Berga?',
        },
    ]


def test_infer_active_after_km_confirmation():
    ctx = infer_establishment_domain_context(
        _patum_bergua_prior_history(),
        'si, 30 km',
    )
    assert ctx.active is True
    assert ctx.destination == 'Berga'
    assert ctx.distance_km == 30


def test_infer_active_for_30_km_des_de_berga():
    ctx = infer_establishment_domain_context(
        _patum_bergua_prior_history(),
        '30 km des de Berga',
    )
    assert ctx.active is True
    assert ctx.destination == 'Berga'
    assert ctx.distance_km == 30


def test_infer_inactive_for_calella_experiences():
    ctx = infer_establishment_domain_context(
        [],
        'Visitas guiadas a 50 km de Calella',
    )
    assert ctx.active is False


def test_infer_active_after_establishments_tool_with_followup():
    history = [
        {'role': 'user', 'content': 'buscam allotjament a prop de Berga'},
        {
            'role': 'assistant',
            'content': [
                {
                    'type': 'tool_use',
                    'id': 'e1',
                    'name': 'search_establishments',
                    'input': {'destination': 'Berga', 'distance_km': 30},
                },
            ],
        },
        {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'e1', 'content': '{}'}]},
        {'role': 'assistant', 'content': 'He trobat allotjaments...'},
    ]
    ctx = infer_establishment_domain_context(history, '2 o 3 més si us plau')
    assert ctx.active is True
    assert ctx.destination == 'Berga'
    assert ctx.distance_km == 30


def test_infer_active_for_short_yes_after_km_question():
    history = [
        {'role': 'user', 'content': 'buscam allotjament a prop de Berga'},
        {
            'role': 'assistant',
            'content': 'A quants km com a màxim vols que busqui des de Berga?',
        },
    ]
    ctx = infer_establishment_domain_context(history, 'si')
    assert ctx.active is True
    assert ctx.destination == 'Berga'


def test_build_establishment_turn_instruction_contains_required_fields():
    ctx = infer_establishment_domain_context(
        _patum_bergua_prior_history(),
        'si, 30 km',
    )
    instruction = build_establishment_turn_instruction(ctx)
    assert "Instrucció d'aquest torn" in instruction
    assert 'search_establishments' in instruction
    assert 'destination: Berga' in instruction
    assert 'distance_km: 30' in instruction
    assert 'search_experiences' in instruction
    assert 'search_articles' in instruction
    assert 'search_events' in instruction


def test_with_system_injects_establishment_instruction():
    service = AgentService(provider='dummy')
    history = _patum_bergua_prior_history() + [{'role': 'user', 'content': 'si, 30 km'}]
    messages = service._with_system(history, 'si, 30 km')
    system_content = messages[0]['content']
    assert "Instrucció d'aquest torn" in system_content
    assert 'search_establishments' in system_content
    assert 'destination: Berga' in system_content
    assert 'distance_km: 30' in system_content


def test_should_not_force_keywords_when_establishment_domain_active():
    history = _patum_bergua_prior_history()
    assert is_establishment_domain_active(history, 'si, 30 km') is True
    assert should_force_keyword_search('si, 30 km', history=history) is False


def test_build_forced_calls_still_works_for_patum_without_establishment_domain():
    history = [
        {'role': 'user', 'content': 'Què en saps de la Patum?'},
    ]
    calls = build_forced_keyword_tool_calls('Què és la Patum?', history=history)
    assert calls is not None
    assert [name for name, _ in calls] == ['search_articles', 'search_events']


def test_fallback_skips_when_establishment_domain_active():
    history = _patum_bergua_prior_history()
    executed = [('search_experiences', {'destination': 'Berga'})]
    assert build_keyword_fallback_calls('si, 30 km', executed, history=history) is None


def test_is_establishment_followup_more_options():
    assert is_establishment_followup_message('2 o 3 mes siusplau') is True
    assert is_establishment_followup_message('2 o 3 més si us plau') is True
