"""Unit tests for app.prompts.femturisme — issue #10 / #11."""
from __future__ import annotations

from app.prompts.femturisme import build_system_prompt
from app.services.tools import ALL_TOOLS


def test_build_system_prompt_lists_registered_tools():
    prompt = build_system_prompt()
    for schema in ALL_TOOLS:
        assert schema['name'] in prompt


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
