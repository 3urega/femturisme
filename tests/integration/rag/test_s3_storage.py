"""Opt-in integration tests against real Supabase S3 storage (issue #35)."""
from __future__ import annotations

import uuid

import pytest

from app.services.document_storage import (
    materialize_original,
    original_exists,
    purge_document_storage,
    save_original,
)
from tests.helpers.env import s3_available

SAMPLE_PDF = b'%PDF-1.4 integration-test'

pytestmark = [
    pytest.mark.s3,
    pytest.mark.skipif(not s3_available(), reason='S3_* credentials not configured'),
]


@pytest.fixture
def s3_config():
    from app.config import Config

    return {
        'STORAGE_BACKEND': 's3',
        'S3_ENDPOINT': Config.S3_ENDPOINT,
        'S3_REGION': Config.S3_REGION,
        'S3_BUCKET': Config.S3_BUCKET,
        'S3_ACCESS_KEY_ID': Config.S3_ACCESS_KEY_ID,
        'S3_SECRET_ACCESS_KEY': Config.S3_SECRET_ACCESS_KEY,
    }


@pytest.fixture
def s3_doc_id(s3_config):
    doc_id = uuid.uuid4()
    save_original(doc_id, SAMPLE_PDF, config=s3_config)
    yield doc_id
    if original_exists(doc_id, config=s3_config):
        purge_document_storage(doc_id, config=s3_config)


def test_s3_round_trip_exists_materialize_purge(s3_config, s3_doc_id):
    assert original_exists(s3_doc_id, config=s3_config)

    with materialize_original(s3_doc_id, config=s3_config) as pdf_path:
        assert pdf_path is not None
        assert pdf_path.read_bytes() == SAMPLE_PDF

    purge_document_storage(s3_doc_id, config=s3_config)
    assert not original_exists(s3_doc_id, config=s3_config)
