"""Unit tests for document storage backends (issue #35)."""
from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.document_storage import (
    build_storage_path,
    materialize_original,
    original_exists,
    purge_document_storage,
    save_original,
)
from app.services.storage_backends import get_storage_backend
from app.services.storage_backends.base import DocumentStorageError
from app.services.storage_backends.s3 import S3StorageBackend

SAMPLE_PDF = b'%PDF-1.4 sample'


@pytest.fixture
def local_config(tmp_path):
    root = tmp_path / 'guides'
    root.mkdir()
    return {
        'STORAGE_BACKEND': 'local',
        'DOCUMENT_STORAGE_PATH': str(root),
    }


def test_local_save_build_path_and_materialize(local_config):
    doc_id = uuid.uuid4()
    save_original(doc_id, SAMPLE_PDF, config=local_config)

    path = build_storage_path(doc_id, config=local_config)
    assert path.endswith(f'{doc_id}/original.pdf')
    assert original_exists(doc_id, config=local_config)

    with materialize_original(doc_id, config=local_config) as pdf_path:
        assert pdf_path is not None
        assert pdf_path.read_bytes() == SAMPLE_PDF


def test_local_purge_removes_file(local_config):
    doc_id = uuid.uuid4()
    save_original(doc_id, SAMPLE_PDF, config=local_config)
    assert original_exists(doc_id, config=local_config)

    purge_document_storage(doc_id, config=local_config)
    assert not original_exists(doc_id, config=local_config)


def test_materialize_missing_returns_none(local_config):
    doc_id = uuid.uuid4()
    with materialize_original(doc_id, config=local_config) as pdf_path:
        assert pdf_path is None


def test_s3_build_storage_path():
    backend = S3StorageBackend(
        {
            'S3_BUCKET': 'guides',
            'S3_ENDPOINT': 'https://example.storage.supabase.co/storage/v1/s3',
            'S3_ACCESS_KEY_ID': 'key',
            'S3_SECRET_ACCESS_KEY': 'secret',
        }
    )
    doc_id = uuid.uuid4()
    assert backend.build_storage_path(doc_id) == f's3://guides/{doc_id}/original.pdf'


@patch('app.services.storage_backends.s3.boto3')
def test_s3_save_put_object(mock_boto3):
    client = MagicMock()
    mock_boto3.client.return_value = client

    doc_id = uuid.uuid4()
    config = {
        'S3_BUCKET': 'guides',
        'S3_ENDPOINT': 'https://example.storage.supabase.co/storage/v1/s3',
        'S3_REGION': 'eu-central-1',
        'S3_ACCESS_KEY_ID': 'key',
        'S3_SECRET_ACCESS_KEY': 'secret',
    }
    backend = get_storage_backend({**config, 'STORAGE_BACKEND': 's3'})
    path = backend.save_original(doc_id, SAMPLE_PDF)

    assert path == f's3://guides/{doc_id}/original.pdf'
    client.put_object.assert_called_once()
    kwargs = client.put_object.call_args.kwargs
    assert kwargs['Bucket'] == 'guides'
    assert kwargs['Key'] == f'{doc_id}/original.pdf'
    assert kwargs['Body'] == SAMPLE_PDF
    mock_boto3.client.assert_called_once()
    call_kwargs = mock_boto3.client.call_args.kwargs
    assert call_kwargs['endpoint_url'] == config['S3_ENDPOINT']
    assert call_kwargs['config'].s3['addressing_style'] == 'path'


@patch('app.services.storage_backends.s3.boto3')
def test_s3_purge_delete_object(mock_boto3):
    client = MagicMock()
    client.head_object.return_value = {}
    mock_boto3.client.return_value = client

    doc_id = uuid.uuid4()
    backend = S3StorageBackend(
        {
            'S3_BUCKET': 'guides',
            'S3_ENDPOINT': 'https://example.storage.supabase.co/storage/v1/s3',
            'S3_ACCESS_KEY_ID': 'key',
            'S3_SECRET_ACCESS_KEY': 'secret',
        }
    )
    backend.purge(doc_id)

    client.head_object.assert_called_once()
    client.delete_object.assert_called_once_with(
        Bucket='guides',
        Key=f'{doc_id}/original.pdf',
    )


@patch('app.services.storage_backends.s3.boto3')
def test_s3_materialize_writes_tempfile(mock_boto3):
    client = MagicMock()
    body = MagicMock()
    body.read.return_value = SAMPLE_PDF
    client.get_object.return_value = {'Body': body}
    client.head_object.return_value = {}
    mock_boto3.client.return_value = client

    doc_id = uuid.uuid4()
    backend = S3StorageBackend(
        {
            'S3_BUCKET': 'guides',
            'S3_ENDPOINT': 'https://example.storage.supabase.co/storage/v1/s3',
            'S3_ACCESS_KEY_ID': 'key',
            'S3_SECRET_ACCESS_KEY': 'secret',
        }
    )

    with backend.materialize_original(doc_id) as pdf_path:
        assert pdf_path is not None
        assert pdf_path.read_bytes() == SAMPLE_PDF
        temp_path = pdf_path

    assert not temp_path.exists()


def test_s3_missing_credentials_raises():
    backend = S3StorageBackend({'STORAGE_BACKEND': 's3', 'S3_BUCKET': 'guides'})
    with pytest.raises(DocumentStorageError, match='S3_ENDPOINT'):
        backend.save_original(uuid.uuid4(), SAMPLE_PDF)
