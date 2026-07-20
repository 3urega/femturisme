"""RAG indexing pipeline integration tests (DEV-504)."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.db.repositories import document_chunks as chunks_repo
from app.db.repositories import documents as documents_repo
from app.services.document_storage import save_original
from app.services.indexing_pipeline import run
from tests.helpers.env import postgres_available

FIXTURES_DIR = Path(__file__).resolve().parents[2] / 'fixtures'
SAMPLE_PDF = FIXTURES_DIR / 'sample-guide.pdf'


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not postgres_available(), reason='POSTGRES_* not configured'),
]


def fake_embed(texts, model=None):
    return [[0.01] * 1536 for _ in texts]


@pytest.fixture
def pipeline_config(app, tmp_path):
    storage_root = tmp_path / 'guides'
    storage_root.mkdir()
    app.config['DOCUMENT_STORAGE_PATH'] = str(storage_root)
    return dict(app.config)


@pytest.fixture
def created_entity_ids(client):
    ids: list[str] = []
    yield ids
    for entity_id in ids:
        client.delete(f'/admin/api/entities/{entity_id}')


def _create_entity(client, created_entity_ids: list[str]) -> dict:
    suffix = uuid.uuid4().hex[:8]
    response = client.post(
        '/admin/api/entities',
        json={
            'name': f'Test entity {suffix}',
            'entity_type': 'museu',
            'slug': f'test-{suffix}',
        },
    )
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    created_entity_ids.append(body['entity_id'])
    return body


def _create_sample_pdf_doc(client, created_entity_ids, pipeline_config) -> dict:
    entity = _create_entity(client, created_entity_ids)
    doc_id = uuid.uuid4()
    pdf_bytes = SAMPLE_PDF.read_bytes()
    storage_path = f"{pipeline_config['DOCUMENT_STORAGE_PATH']}/{doc_id}/original.pdf"
    document = documents_repo.create(
        doc_id=doc_id,
        entity_id=entity['entity_id'],
        title='Guia pipeline',
        category='patrimoni',
        source_filename='sample-guide.pdf',
        storage_path=storage_path,
        config=pipeline_config,
    )
    save_original(doc_id, pdf_bytes, config=pipeline_config)
    return document


def _create_empty_pdf_doc(client, created_entity_ids, pipeline_config) -> dict:
    entity = _create_entity(client, created_entity_ids)
    doc_id = uuid.uuid4()
    documents_repo.create(
        doc_id=doc_id,
        entity_id=entity['entity_id'],
        title='PDF buit',
        source_filename='empty.pdf',
        storage_path=f"{pipeline_config['DOCUMENT_STORAGE_PATH']}/{doc_id}/original.pdf",
        config=pipeline_config,
    )

    try:
        import fitz
    except ImportError:
        pytest.skip('pymupdf not installed')

    empty_doc = fitz.open()
    empty_doc.new_page()
    pdf_bytes = empty_doc.tobytes()
    empty_doc.close()
    save_original(doc_id, pdf_bytes, config=pipeline_config)
    return documents_repo.get_by_id(doc_id, config=pipeline_config)


def test_pipeline_indexes_sample_pdf(client, pipeline_config, created_entity_ids):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']

    run(doc_id, config=pipeline_config, embedder=fake_embed)

    document = documents_repo.get_by_id(doc_id, config=pipeline_config)
    assert document['status'] == 'indexed'
    assert document['pages_count'] > 0
    assert document['chunks_count'] > 0
    assert document['embedded_chunks_count'] == document['chunks_count']
    assert document['embedding_model'] == pipeline_config['EMBEDDING_MODEL']
    assert document['indexed_at'] is not None
    assert chunks_repo.count_by_doc_id(doc_id, config=pipeline_config) == document['chunks_count']


def test_pipeline_fails_on_empty_pdf(client, pipeline_config, created_entity_ids):
    document = _create_empty_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = document['doc_id']

    with pytest.raises(Exception):
        run(doc_id, config=pipeline_config, embedder=fake_embed)

    failed = documents_repo.get_by_id(doc_id, config=pipeline_config)
    assert failed['status'] == 'failed'
    assert failed['error_message']
    assert chunks_repo.count_by_doc_id(doc_id, config=pipeline_config) == 0


def test_reindex_replaces_chunks_and_increments_version(
    client,
    pipeline_config,
    created_entity_ids,
):
    uploaded = _create_sample_pdf_doc(client, created_entity_ids, pipeline_config)
    doc_id = uploaded['doc_id']

    run(doc_id, config=pipeline_config, embedder=fake_embed)
    first = documents_repo.get_by_id(doc_id, config=pipeline_config)
    first_count = chunks_repo.count_by_doc_id(doc_id, config=pipeline_config)

    run(doc_id, reindex=True, config=pipeline_config, embedder=fake_embed)
    second = documents_repo.get_by_id(doc_id, config=pipeline_config)

    assert second['status'] == 'indexed'
    assert second['version'] == first['version'] + 1
    assert second['chunks_count'] > 0
    assert chunks_repo.count_by_doc_id(doc_id, config=pipeline_config) == second['chunks_count']
    assert second['chunks_count'] == first_count
