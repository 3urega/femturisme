"""Shared pytest fixtures."""
from __future__ import annotations

import json

import pytest
from dotenv import load_dotenv

load_dotenv()

from app import create_app


@pytest.fixture
def app():
    """Flask app in testing mode."""
    application = create_app('testing')
    yield application


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_tool_execute(monkeypatch):
    """Return fixed JSON from execute_tool (no scraping / network)."""

    def _fake_execute(name: str, tool_input: dict) -> str:
        return json.dumps({
            'destination': tool_input.get('destination', 'Catalunya'),
            'total': '1',
            'results': [{
                'title': 'Resultat prova',
                'location': 'Catalunya',
                'url': 'https://www.femturisme.cat/prova',
                'description': 'Test',
            }],
            'error': None,
        })

    monkeypatch.setattr('app.services.tools.execute_tool', _fake_execute)
    monkeypatch.setattr('app.services.agent_service.execute_tool', _fake_execute)
