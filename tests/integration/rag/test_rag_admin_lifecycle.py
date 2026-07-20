"""RAG admin lifecycle integration tests — tecnic §14.4 gaps (DEV-507)."""
from __future__ import annotations

import uuid

import pytest

from app.db.repositories import document_chunks as chunks_repo
from app.db.repositories import documents as documents_repo
from app.services.document_storage import document_dir, original_file_path
from app.services.indexing_pipeline import run
from tests.integration.rag.test_indexing_pipeline import (
    _create_empty_pdf_doc,
    _create_sample_pdf_doc,
    fake_embed,
    pipeline_config,
)
from tests.helpers.env import postgres_available

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured'),
]


@pytest.fixture
def created_entity_ids(client):
    ids: list[str] = []
    yield ids
    for entity_id in ids:
        client.delete(f'/admin/api/entities/{entity_id}')


def test_delete_document_removes_chunks(
    client,
    pipeline_config,
    created_entity_ids,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']

    run(doc_id, config=pipeline_config, embedder=fake_embed)
    assert chunks_repo.count_by_doc_id(doc_id, config=pipeline_config) > 0

    response = client.delete(f'/admin/api/documents/{doc_id}')
    assert response.status_code == 200

    assert documents_repo.get_by_id(doc_id, config=pipeline_config) is None
    assert chunks_repo.count_by_doc_id(doc_id, config=pipeline_config) == 0


def test_delete_entity_cascades_documents(
    client,
    pipeline_config,
    created_entity_ids,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']
    entity_id = uploaded['entity_id']

    response = client.delete(f'/admin/api/entities/{entity_id}')
    assert response.status_code == 200

    assert documents_repo.get_by_id(doc_id, config=pipeline_config) is None
    detail = client.get(f'/admin/api/documents/{doc_id}')
    assert detail.status_code == 404


def test_failed_document_excluded_from_search(
    client,
    pipeline_config,
    created_entity_ids,
    monkeypatch,
):
    document = _create_empty_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = document['doc_id']

    with pytest.raises(Exception):
        run(doc_id, config=pipeline_config, embedder=fake_embed)

    failed = documents_repo.get_by_id(doc_id, config=pipeline_config)
    assert failed['status'] == 'failed'

    monkeypatch.setattr(
        'app.services.embedding_service.EmbeddingService.embed_texts',
        lambda self, texts, model=None: fake_embed(texts, model),
    )

    result = documents_repo.search(
        query='on aparcar',
        entity_id=document['entity_id'],
        config=pipeline_config,
        embedder=fake_embed,
    )
    assert result['total'] == 0
    assert result['results'] == []


def test_delete_entity_removes_pdf_from_disk(
    client,
    pipeline_config,
    created_entity_ids,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']
    entity_id = uploaded['entity_id']
    pdf_path = original_file_path(doc_id, config=pipeline_config)
    assert pdf_path.is_file()

    response = client.delete(f'/admin/api/entities/{entity_id}')
    assert response.status_code == 200
    assert not document_dir(doc_id, config=pipeline_config).exists()


def test_upload_rejects_inactive_entity(
    client,
    pipeline_config,
    created_entity_ids,
):
    from pathlib import Path

    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    entity_id = uploaded['entity_id']

    deactivated = client.put(
        f'/admin/api/entities/{entity_id}',
        json={'is_active': False},
    )
    assert deactivated.status_code == 200

    sample_pdf = Path(__file__).resolve().parents[2] / 'fixtures' / 'sample-guide.pdf'
    with sample_pdf.open('rb') as handle:
        response = client.post(
            '/admin/api/documents/upload',
            data={
                'entity_id': entity_id,
                'title': 'Inactive upload',
                'file': (handle, 'sample-guide.pdf'),
            },
            content_type='multipart/form-data',
        )

    assert response.status_code == 400
    assert 'not active' in response.get_json()['error']
