"""Storage backend factory for guide PDF originals."""
from __future__ import annotations

from typing import Any, Mapping

from app.services.storage_backends.base import StorageBackend, resolve_storage_config
from app.services.storage_backends.local import LocalStorageBackend
from app.services.storage_backends.s3 import S3StorageBackend


def get_storage_backend(config: Mapping[str, Any] | None = None) -> StorageBackend:
    """Return configured storage backend (local default)."""
    resolved = resolve_storage_config(config)
    backend_name = str(resolved.get('STORAGE_BACKEND', 'local') or 'local').strip().lower()
    if backend_name == 's3':
        return S3StorageBackend(resolved)
    return LocalStorageBackend(resolved)


__all__ = [
    'StorageBackend',
    'get_storage_backend',
    'resolve_storage_config',
    'LocalStorageBackend',
    'S3StorageBackend',
]
