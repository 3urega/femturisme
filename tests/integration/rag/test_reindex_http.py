"""HTTP reindex integration tests — tecnic §14.4 (issue #34)."""
from __future__ import annotations

import time

import pytest

from app.db.repositories import documents as documents_repo
from app.services.document_storage import save_original
from app.services.indexing_pipeline import run
from tests.helpers.env import postgres_available
from tests.integration.rag.test_indexing_pipeline import (
    SAMPLE_PDF,
    _create_empty_pdf_doc,
    _create_sample_pdf_doc,
    fake_embed,
    pipeline_config,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured'),
]

POLL_TIMEOUT_SECONDS = 30
POLL_INTERVAL_SECONDS = 0.2


@pytest.fixture
def created_entity_ids(client):
    ids: list[str] = []
    yield ids
    for entity_id in ids:
        client.delete(f'/admin/api/entities/{entity_id}')


@pytest.fixture
def fake_embedding_service(monkeypatch):
    monkeypatch.setattr(
        'app.services.embedding_service.EmbeddingService.embed_texts',
        lambda self, texts, model=None: fake_embed(texts, model),
    )


def _poll_until_indexed(doc_id, *, pipeline_config, timeout=POLL_TIMEOUT_SECONDS) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        document = documents_repo.get_by_id(doc_id, config=pipeline_config)
        assert document is not None
        status = document.get('status')
        if status == 'indexed':
            return document
        if status == 'failed':
            pytest.fail(document.get('error_message') or 'indexing failed')
        time.sleep(POLL_INTERVAL_SECONDS)
    pytest.fail(f'timed out waiting for indexed status for doc_id={doc_id}')


def test_reindex_http_increments_version(
    client,
    pipeline_config,
    created_entity_ids,
    fake_embedding_service,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']

    run(doc_id, config=pipeline_config, embedder=fake_embed)
    first = documents_repo.get_by_id(doc_id, config=pipeline_config)
    version_before = int(first['version'])

    response = client.post(f'/admin/api/documents/{doc_id}/reindex')
    assert response.status_code == 202

    second = _poll_until_indexed(doc_id, pipeline_config=pipeline_config)
    assert second['version'] == version_before + 1


def test_failed_document_reindex_via_http(
    client,
    pipeline_config,
    created_entity_ids,
    fake_embedding_service,
):
    document = _create_empty_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = document['doc_id']

    with pytest.raises(Exception):
        run(doc_id, config=pipeline_config, embedder=fake_embed)

    failed = documents_repo.get_by_id(doc_id, config=pipeline_config)
    assert failed['status'] == 'failed'

    save_original(doc_id, SAMPLE_PDF.read_bytes(), config=pipeline_config)

    response = client.post(f'/admin/api/documents/{doc_id}/reindex')
    assert response.status_code == 202

    indexed = _poll_until_indexed(doc_id, pipeline_config=pipeline_config)
    assert indexed['status'] == 'indexed'
    assert indexed['chunks_count'] > 0
