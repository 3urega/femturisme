"""S3-compatible storage backend (Supabase Storage, issue #35)."""
from __future__ import annotations

import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from app.services.storage_backends.base import DocumentStorageError, StorageBackend


def _object_key(doc_id: str | uuid.UUID) -> str:
    return f'{doc_id}/original.pdf'


class S3StorageBackend(StorageBackend):
    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        cfg = dict(config or {})
        self._endpoint = str(cfg.get('S3_ENDPOINT', '') or '').strip()
        self._region = str(cfg.get('S3_REGION', 'eu-central-1') or 'eu-central-1')
        self._bucket = str(cfg.get('S3_BUCKET', 'guides') or 'guides')
        self._access_key = str(cfg.get('S3_ACCESS_KEY_ID', '') or '').strip()
        self._secret_key = str(cfg.get('S3_SECRET_ACCESS_KEY', '') or '').strip()
        self._client = None

    def _validate_config(self) -> None:
        missing = []
        if not self._endpoint:
            missing.append('S3_ENDPOINT')
        if not self._access_key:
            missing.append('S3_ACCESS_KEY_ID')
        if not self._secret_key:
            missing.append('S3_SECRET_ACCESS_KEY')
        if not self._bucket:
            missing.append('S3_BUCKET')
        if missing:
            raise DocumentStorageError(
                f'S3 storage requires: {", ".join(missing)} (STORAGE_BACKEND=s3)'
            )

    def _get_client(self):
        if self._client is not None:
            return self._client
        self._validate_config()
        try:
            import boto3
            from botocore.config import Config as BotoConfig
        except ImportError as exc:
            raise DocumentStorageError('boto3 is not installed') from exc

        self._client = boto3.client(
            's3',
            endpoint_url=self._endpoint,
            region_name=self._region,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            config=BotoConfig(s3={'addressing_style': 'path'}),
        )
        return self._client

    def build_storage_path(self, doc_id: str | uuid.UUID) -> str:
        return f's3://{self._bucket}/{_object_key(doc_id)}'

    def save_original(self, doc_id: str | uuid.UUID, data: bytes) -> str:
        client = self._get_client()
        try:
            client.put_object(
                Bucket=self._bucket,
                Key=_object_key(doc_id),
                Body=data,
                ContentType='application/pdf',
            )
        except Exception as exc:
            raise DocumentStorageError(str(exc)) from exc
        return self.build_storage_path(doc_id)

    def read_bytes(self, doc_id: str | uuid.UUID) -> bytes:
        client = self._get_client()
        try:
            response = client.get_object(
                Bucket=self._bucket,
                Key=_object_key(doc_id),
            )
            return response['Body'].read()
        except Exception as exc:
            raise DocumentStorageError(str(exc)) from exc

    def exists(self, doc_id: str | uuid.UUID) -> bool:
        client = self._get_client()
        try:
            client.head_object(Bucket=self._bucket, Key=_object_key(doc_id))
            return True
        except Exception as exc:
            try:
                from botocore.exceptions import ClientError

                if isinstance(exc, ClientError):
                    code = exc.response.get('Error', {}).get('Code', '')
                    if code in ('404', 'NoSuchKey', 'NotFound'):
                        return False
            except ImportError:
                pass
            raise DocumentStorageError(str(exc)) from exc

    def purge(self, doc_id: str | uuid.UUID) -> None:
        if not self.exists(doc_id):
            return
        client = self._get_client()
        try:
            client.delete_object(Bucket=self._bucket, Key=_object_key(doc_id))
        except Exception as exc:
            raise DocumentStorageError(str(exc)) from exc

    @contextmanager
    def _materialize_original_path(self, doc_id: str | uuid.UUID) -> Iterator[Path]:
        data = self.read_bytes(doc_id)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as handle:
                handle.write(data)
                temp_path = Path(handle.name)
            yield temp_path
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
