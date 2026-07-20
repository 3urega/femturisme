"""Admin API and UI authentication tests (issue #34)."""
from __future__ import annotations

import pytest

from app.services.admin_auth import ADMIN_TOKEN_COOKIE

pytestmark = pytest.mark.integration

TEST_TOKEN = 'test-admin-token-secret'


@pytest.fixture
def admin_token_app(app):
    app.config['ADMIN_API_TOKEN'] = TEST_TOKEN
    return app


def test_admin_api_entities_requires_token(admin_token_app):
    client = admin_token_app.test_client()
    response = client.get('/admin/api/entities')
    assert response.status_code == 401
    assert response.get_json()['error'] == 'unauthorized'


def test_admin_api_entities_accepts_bearer(admin_token_app):
    client = admin_token_app.test_client()
    response = client.get(
        '/admin/api/entities',
        headers={'Authorization': f'Bearer {TEST_TOKEN}'},
    )
    assert response.status_code == 200


def test_admin_guides_requires_auth(admin_token_app):
    client = admin_token_app.test_client()
    response = client.get('/admin/guides')
    assert response.status_code == 401


def test_admin_guides_accepts_cookie(admin_token_app):
    client = admin_token_app.test_client()
    response = client.get(
        '/admin/guides',
        headers={'Cookie': f'{ADMIN_TOKEN_COOKIE}={TEST_TOKEN}'},
    )
    assert response.status_code == 200
    assert b'Guies PDF' in response.data
