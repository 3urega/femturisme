"""Unit tests for app.prompts.femturisme — issue #10 / #11."""
from __future__ import annotations

from app.prompts.femturisme import build_page_context_section, build_system_prompt
from app.services.chat_context import AgentContext, PageContext
from app.services.tools import CATALOG_TOOLS


def test_build_system_prompt_lists_catalog_tools_only():
    prompt = build_system_prompt()
    for schema in CATALOG_TOOLS:
        assert schema['name'] in prompt
    assert 'search_local_knowledge' not in prompt
    assert 'search_entity_knowledge' not in prompt


def test_build_system_prompt_no_scraping_or_legacy():
    prompt = build_system_prompt()
    assert 'scraping' not in prompt.lower()
    assert 'search_accommodations' not in prompt


def test_build_system_prompt_agenda_vs_experiences():
    prompt = build_system_prompt()
    assert 'search_events' in prompt
    assert 'search_experiences' in prompt
    assert 'Agenda' in prompt or 'agenda' in prompt
    assert 'promocional' in prompt.lower() or 'PROMOCIONAL' in prompt


def test_build_system_prompt_articles_available():
    prompt = build_system_prompt()
    assert 'search_articles' in prompt
    assert 'pendent' not in prompt.lower()
    assert 'encara no disponible' not in prompt.lower()
    assert 'notícies' in prompt.lower() or 'noticies' in prompt.lower()


def test_build_system_prompt_articles_vs_agenda():
    prompt = build_system_prompt()
    assert 'search_articles' in prompt
    assert 'Articles / notícies' in prompt or 'articles editorials' in prompt.lower()
    assert 'search_events' in prompt
    assert 'search_destinations' in prompt


def test_build_system_prompt_ca08_and_meta():
    prompt = build_system_prompt()
    assert 'CA-08' in prompt
    assert 'meta.scope' in prompt or 'meta' in prompt
    assert 'territory_wide' in prompt
    assert 'zero_results_with_location' in prompt


def test_build_system_prompt_broad_territory():
    from datetime import date

    prompt = build_system_prompt(today=date(2026, 7, 13))
    assert 'Catalunya' in prompt
    assert 'date_from' in prompt
    assert 'date_to' in prompt
    assert '2026-07-13' in prompt
    assert '2026-07-01' in prompt


def test_build_system_prompt_catalan_language_rules():
    prompt = build_system_prompt()
    assert "digues-m'ho" in prompt
    assert 'dime-ho' in prompt
    assert 'no barregis' in prompt.lower() or 'no barregis' in prompt


def test_build_system_prompt_establishments_query_for_dishes():
    prompt = build_system_prompt()
    assert 'query' in prompt
    assert 'macarrons' in prompt
    assert 'search_experiences' in prompt
    assert 'zero_results_text_query' in prompt
    assert 'fallback_results' in prompt


def test_build_system_prompt_establishments_cuisine_vs_dish_routing():
    prompt = build_system_prompt()
    assert 'Cuina / estil vs plat concret' in prompt
    assert 'cuina catalana tradicional' in prompt
    assert 'sense' in prompt.lower() and 'query' in prompt
    assert 'literal' in prompt.lower() or 'coincidències' in prompt.lower()
    assert 'macarrons' in prompt
    assert 'type=restaurant' in prompt


def test_build_page_context_section_includes_navigation_fields():
    section = build_page_context_section(PageContext(
        section='agenda',
        ubicacio='Empordà',
        municipality='Pals',
    ))
    assert 'Context de pàgina' in section
    assert 'agenda' in section
    assert 'Empordà' in section
    assert 'Pals' in section


def test_build_system_prompt_with_page_context():
    prompt = build_system_prompt(page_context=PageContext(
        section='agenda',
        ubicacio='Empordà',
        municipality='Pals',
    ))
    assert 'Context de pàgina' in prompt
    assert 'Empordà' in prompt


def test_build_system_prompt_without_page_context_omits_block():
    prompt = build_system_prompt()
    assert 'Context de pàgina' not in prompt


def test_build_system_prompt_femturisme_agent_context():
    prompt = build_system_prompt(agent_context=AgentContext(mode='femturisme'))
    assert 'Mode **femturisme**' in prompt


def test_build_system_prompt_user_language_french():
    prompt = build_system_prompt(user_language='fr')
    assert 'Idioma detectat' in prompt
    assert 'fr' in prompt
    assert 'francès' in prompt


def test_build_system_prompt_user_language_spanish():
    prompt = build_system_prompt(user_language='es')
    assert 'Idioma detectat' in prompt
    assert 'castellà' in prompt
