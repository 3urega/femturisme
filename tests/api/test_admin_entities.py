"""Admin entities API integration tests (DEV-501)."""
from __future__ import annotations

import uuid

import pytest

from tests.helpers.env import postgres_available


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured'),
]


@pytest.fixture
def created_entity_ids(client):
    """Track entities created during a test and delete them afterward."""
    ids: list[str] = []
    yield ids
    for entity_id in ids:
        client.delete(f'/admin/api/entities/{entity_id}')


def _create_entity(client, *, slug_suffix: str | None = None) -> dict:
    suffix = slug_suffix or uuid.uuid4().hex[:8]
    payload = {
        'name': f'Test entity {suffix}',
        'entity_type': 'museu',
        'slug': f'test-{suffix}',
        'territory': 'Berguedà',
        'config': {'source': 'pytest'},
    }
    response = client.post('/admin/api/entities', json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def test_admin_create_and_get_entity(client, created_entity_ids):
    created = _create_entity(client)
    entity_id = created['entity_id']
    created_entity_ids.append(entity_id)

    assert uuid.UUID(entity_id)
    assert created['name'].startswith('Test entity ')
    assert created['entity_type'] == 'museu'
    assert created['is_active'] is True
    assert created['config'] == {'source': 'pytest'}

    detail = client.get(f'/admin/api/entities/{entity_id}')
    assert detail.status_code == 200
    body = detail.get_json()
    assert body['entity_id'] == entity_id
    assert body['slug'] == created['slug']


def test_admin_list_entities_includes_created(client, created_entity_ids):
    created = _create_entity(client)
    created_entity_ids.append(created['entity_id'])

    listing = client.get('/admin/api/entities')
    assert listing.status_code == 200
    body = listing.get_json()
    assert 'entities' in body
    assert 'total' in body
    assert body['total'] == len(body['entities'])
    ids = {row['entity_id'] for row in body['entities']}
    assert created['entity_id'] in ids


def test_admin_delete_entity_returns_ok(client):
    created = _create_entity(client)
    entity_id = created['entity_id']

    deleted = client.delete(f'/admin/api/entities/{entity_id}')
    assert deleted.status_code == 200
    assert deleted.get_json() == {'ok': True}

    missing = client.get(f'/admin/api/entities/{entity_id}')
    assert missing.status_code == 404


def test_admin_rejects_invalid_entity_type(client):
    response = client.post(
        '/admin/api/entities',
        json={'name': 'Invalid type', 'entity_type': 'not-a-valid-type'},
    )
    assert response.status_code == 400
    assert 'entity_type' in response.get_json()['error']
