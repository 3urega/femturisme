"""RAG semantic search integration tests (DEV-505)."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.db.repositories import documents as documents_repo
from app.services.document_storage import save_original
from app.services.indexing_pipeline import run
from tests.helpers.env import postgres_available
from tests.integration.rag.test_indexing_pipeline import (
    _create_entity,
    _create_sample_pdf_doc,
    fake_embed,
    pipeline_config,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / 'fixtures'
SAMPLE_PDF = FIXTURES_DIR / 'sample-guide.pdf'


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


def _index_sample_doc(client, created_entity_ids, pipeline_config) -> dict:
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    run(uploaded['doc_id'], config=pipeline_config, embedder=fake_embed)
    return documents_repo.get_by_id(uploaded['doc_id'], config=pipeline_config)


def test_search_returns_chunks_for_indexed_entity(
    client,
    pipeline_config,
    created_entity_ids,
):
    document = _index_sample_doc(client, created_entity_ids, pipeline_config)

    result = documents_repo.search(
        query='on aparcar',
        entity_id=document['entity_id'],
        config=pipeline_config,
        embedder=fake_embed,
    )

    assert result['total'] >= 1
    assert result['entity_id'] == document['entity_id']
    hit = result['results'][0]
    assert hit['content']
    assert hit['summary']
    assert hit['doc_id'] == document['doc_id']
    assert hit['metadata']['doc_title'] == 'Guia pipeline'
    assert hit['metadata']['source_file'] == 'sample-guide.pdf'


def test_search_filters_by_entity_id(client, pipeline_config, created_entity_ids):
    document = _index_sample_doc(client, created_entity_ids, pipeline_config)
    other_entity = _create_entity(client, created_entity_ids)

    result = documents_repo.search(
        query='on aparcar',
        entity_id=other_entity['entity_id'],
        config=pipeline_config,
        embedder=fake_embed,
    )

    assert result['total'] == 0
    assert result['results'] == []
    assert document['entity_id'] != other_entity['entity_id']


def test_smoke_test_endpoint_returns_results(
    client,
    pipeline_config,
    created_entity_ids,
    monkeypatch,
):
    document = _index_sample_doc(client, created_entity_ids, pipeline_config)

    monkeypatch.setattr(
        'app.services.embedding_service.EmbeddingService.embed_texts',
        lambda self, texts, model=None: fake_embed(texts, model),
    )

    response = client.post(
        f"/admin/api/documents/{document['doc_id']}/smoke-test",
        json={'query': 'on aparcar'},
    )

    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body['total'] >= 1
    assert body['entity_id'] == document['entity_id']
    assert body['results'][0]['content']


def test_search_skips_non_indexed_documents(
    client,
    pipeline_config,
    created_entity_ids,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)

    result = documents_repo.search(
        query='on aparcar',
        entity_id=uploaded['entity_id'],
        config=pipeline_config,
        embedder=fake_embed,
    )
    assert result['total'] == 0

    response = client.post(
        f"/admin/api/documents/{uploaded['doc_id']}/smoke-test",
        json={'query': 'on aparcar'},
    )
    assert response.status_code == 400
    assert 'not indexed' in response.get_json()['error']
