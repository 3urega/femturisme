"""Unit tests for query keyword extraction — issue #37."""
from __future__ import annotations

from app.services.query_keywords import (
    build_forced_keyword_tool_calls,
    is_establishment_followup_message,
    primary_search_keyword,
    should_force_keyword_search,
)


def test_primary_keyword_patum():
    assert primary_search_keyword('Què és la Patum?') == 'patum'


def test_primary_keyword_castellers_barcelona():
    assert primary_search_keyword('Articles sobre castellers a Barcelona') == 'castellers'


def test_primary_keyword_fira_medieval_pals():
    keyword = primary_search_keyword('Quan és la Fira medieval de Pals?')
    assert keyword is not None
    assert 'fira' in keyword
    assert 'medieval' in keyword


def test_should_not_force_destination_query():
    assert should_force_keyword_search('Què veure a Besalú?') is False


def test_should_not_force_greeting():
    assert should_force_keyword_search('Hola') is False
    assert primary_search_keyword('Hola') is None


def test_build_forced_calls_patum():
    calls = build_forced_keyword_tool_calls('Què és la Patum?')
    assert calls is not None
    assert len(calls) == 2
    names = [name for name, _ in calls]
    assert names == ['search_articles', 'search_events']
    for _, tool_input in calls:
        assert tool_input.get('query') == 'patum'


def test_build_forced_calls_castellers_includes_destination():
    calls = build_forced_keyword_tool_calls('Articles sobre castellers a Barcelona')
    assert calls is not None
    articles_input = dict(calls[0][1])
    assert articles_input['query'] == 'castellers'
    assert articles_input.get('destination') == 'Barcelona'


def test_build_forced_calls_skips_agenda_query():
    message = "Què fer aquest cap de setmana a l'Empordà?"
    assert build_forced_keyword_tool_calls(message) is None


def test_is_establishment_followup_more_options():
    assert is_establishment_followup_message('2 o 3 mes siusplau') is True
    assert is_establishment_followup_message('2 o 3 més si us plau') is True


def test_should_not_force_establishment_followup_more_options():
    assert should_force_keyword_search('2 o 3 mes siusplau') is False
    assert should_force_keyword_search('2 o 3 més si us plau') is False


def test_should_not_force_establishment_followup_short_yes():
    assert should_force_keyword_search('si') is False
    assert should_force_keyword_search('Sí, endavant') is True  # not a bare follow-up
    assert is_establishment_followup_message('si') is True
    assert is_establishment_followup_message('Sí, endavant') is False


def test_build_forced_calls_skips_establishment_followup():
    assert build_forced_keyword_tool_calls('2 o 3 mes siusplau') is None
    assert build_forced_keyword_tool_calls('no cal que siguin rurals') is None
