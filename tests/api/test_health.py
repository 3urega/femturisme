"""API tests for GET /health — tecnic.md §9.3, API-05."""
from __future__ import annotations


def test_api_05_health_returns_200_json(client):
    """API-05: GET /health → 200 with service and database status."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.content_type.startswith('application/json')

    data = response.get_json()
    assert data is not None
    assert data['ok'] is True
    assert data['service'] == 'up'
    assert data['mysql']['status'] in ('not_configured', 'ok')
    assert data['postgres']['status'] == 'not_configured'
