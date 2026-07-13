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
