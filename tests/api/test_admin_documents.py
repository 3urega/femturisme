"""Admin documents API integration tests (DEV-502, DEV-503)."""
from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest

from app.services.document_storage import original_file_path
from tests.helpers.env import postgres_available

FIXTURES_DIR = Path(__file__).resolve().parent.parent / 'fixtures'
SAMPLE_PDF = FIXTURES_DIR / 'sample-guide.pdf'


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured'),
]


@pytest.fixture
def document_storage_path(app, tmp_path):
    """Use an isolated storage directory for each test."""
    storage_root = tmp_path / 'guides'
    storage_root.mkdir()
    app.config['DOCUMENT_STORAGE_PATH'] = str(storage_root)
    return storage_root


@pytest.fixture
def created_entity_ids(client):
    ids: list[str] = []
    yield ids
    for entity_id in ids:
        client.delete(f'/admin/api/entities/{entity_id}')


def _create_entity(client, created_entity_ids: list[str]) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {
        'name': f'Test entity {suffix}',
        'entity_type': 'museu',
        'slug': f'test-{suffix}',
    }
    response = client.post('/admin/api/entities', json=payload)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    created_entity_ids.append(body['entity_id'])
    return body


def _upload_document(client, entity_id: str, *, title: str = 'Guia prova') -> dict:
    with SAMPLE_PDF.open('rb') as handle:
        response = client.post(
            '/admin/api/documents/upload',
            data={
                'entity_id': entity_id,
                'title': title,
                'category': 'patrimoni',
                'file': (handle, 'sample-guide.pdf'),
            },
            content_type='multipart/form-data',
        )
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def test_admin_upload_creates_pending_document_and_file(
    client,
    document_storage_path,
    created_entity_ids,
):
    entity = _create_entity(client, created_entity_ids)
    document = _upload_document(client, entity['entity_id'])

    assert uuid.UUID(document['doc_id'])
    assert document['entity_id'] == entity['entity_id']
    assert document['title'] == 'Guia prova'
    assert document['category'] == 'patrimoni'
    assert document['status'] == 'pending'
    assert document['pages_count'] == 0
    assert document['chunks_count'] == 0
    assert document['embedded_chunks_count'] == 0
    assert document['source_filename'] == 'sample-guide.pdf'
    assert document['storage_path'].endswith(f"/{document['doc_id']}/original.pdf")

    pdf_path = original_file_path(document['doc_id'], config={'DOCUMENT_STORAGE_PATH': str(document_storage_path)})
    assert pdf_path.is_file()
    assert pdf_path.read_bytes().startswith(b'%PDF')


def test_admin_list_and_get_document(client, document_storage_path, created_entity_ids):
    entity = _create_entity(client, created_entity_ids)
    created = _upload_document(client, entity['entity_id'], title='Guia llistat')

    listing = client.get('/admin/api/documents')
    assert listing.status_code == 200
    list_body = listing.get_json()
    assert 'documents' in list_body
    assert 'total' in list_body
    assert list_body['total'] == len(list_body['documents'])
    assert any(row['doc_id'] == created['doc_id'] for row in list_body['documents'])

    filtered = client.get(f"/admin/api/documents?entity_id={entity['entity_id']}")
    assert filtered.status_code == 200
    filtered_body = filtered.get_json()
    assert all(row['entity_id'] == entity['entity_id'] for row in filtered_body['documents'])

    detail = client.get(f"/admin/api/documents/{created['doc_id']}")
    assert detail.status_code == 200
    detail_body = detail.get_json()
    assert detail_body['doc_id'] == created['doc_id']
    assert detail_body['title'] == 'Guia llistat'


def test_admin_delete_document_removes_row_and_file(
    client,
    document_storage_path,
    created_entity_ids,
):
    entity = _create_entity(client, created_entity_ids)
    created = _upload_document(client, entity['entity_id'])
    doc_id = created['doc_id']

    deleted = client.delete(f'/admin/api/documents/{doc_id}')
    assert deleted.status_code == 200
    assert deleted.get_json() == {'ok': True}

    missing = client.get(f'/admin/api/documents/{doc_id}')
    assert missing.status_code == 404

    pdf_path = original_file_path(doc_id, config={'DOCUMENT_STORAGE_PATH': str(document_storage_path)})
    assert not pdf_path.exists()


def test_admin_upload_rejects_missing_entity(client, document_storage_path):
    missing_entity_id = str(uuid.uuid4())
    with SAMPLE_PDF.open('rb') as handle:
        response = client.post(
            '/admin/api/documents/upload',
            data={
                'entity_id': missing_entity_id,
                'title': 'Guia prova',
                'file': (handle, 'sample-guide.pdf'),
            },
            content_type='multipart/form-data',
        )
    assert response.status_code == 404
    assert response.get_json()['error'] == 'entity not found'


def test_admin_upload_rejects_non_pdf(client, document_storage_path, created_entity_ids):
    entity = _create_entity(client, created_entity_ids)
    response = client.post(
        '/admin/api/documents/upload',
        data={
            'entity_id': entity['entity_id'],
            'title': 'No es PDF',
            'file': (io.BytesIO(b'not-a-pdf'), 'notes.txt', 'text/plain'),
        },
        content_type='multipart/form-data',
    )
    assert response.status_code == 400
    assert 'PDF' in response.get_json()['error']
