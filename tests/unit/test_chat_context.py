"""Unit tests — chat_context parsing and validation."""
from __future__ import annotations

import pytest

from app.services.chat_context import (
    AgentContext,
    ChatContextError,
    EntityModeNotAvailableError,
    PageContext,
    parse_chat_request,
    validate_agent_context,
)


def test_parse_defaults_femturisme_mode():
    message, session_id, page, agent = parse_chat_request({
        'message': 'Hola',
        'session_id': 'abc-123',
    })
    assert message == 'Hola'
    assert session_id == 'abc-123'
    assert page is None
    assert agent == AgentContext(mode='femturisme', entity_id=None)


def test_parse_page_context_partial():
    _, _, page, _ = parse_chat_request({
        'message': 'Què fer aquí?',
        'page_context': {
            'section': 'agenda',
            'ubicacio': 'Empordà',
            'municipality': 'Pals',
            'extra': 'ignored',
        },
    })
    assert page == PageContext(
        section='agenda',
        ubicacio='Empordà',
        municipality='Pals',
    )


def test_parse_page_context_empty_object_is_none():
    _, _, page, _ = parse_chat_request({
        'message': 'Hola',
        'page_context': {},
    })
    assert page is None


def test_parse_explicit_femturisme_agent_context():
    _, _, _, agent = parse_chat_request({
        'message': 'Hola',
        'agent_context': {'mode': 'femturisme', 'entity_id': None},
    })
    assert agent.mode == 'femturisme'
    assert agent.entity_id is None


def test_validate_entitat_without_entity_id_raises_400():
    with pytest.raises(ChatContextError, match='entity_id'):
        validate_agent_context(AgentContext(mode='entitat', entity_id=None))


def test_validate_entitat_invalid_uuid_raises_400():
    with pytest.raises(ChatContextError, match='UUID'):
        validate_agent_context(AgentContext(mode='entitat', entity_id='not-a-uuid'))


def test_validate_entitat_with_valid_uuid_raises_501():
    entity_id = '550e8400-e29b-41d4-a716-446655440000'
    with pytest.raises(EntityModeNotAvailableError, match='Fase 1'):
        validate_agent_context(AgentContext(mode='entitat', entity_id=entity_id))


def test_parse_invalid_mode_raises():
    with pytest.raises(ChatContextError, match='mode'):
        parse_chat_request({
            'message': 'Hola',
            'agent_context': {'mode': 'unknown'},
        })
