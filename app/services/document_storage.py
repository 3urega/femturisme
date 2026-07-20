"""Storage facade for uploaded guide PDFs (DEV-503, issue #35).

Backends: local disc (default) or Supabase S3-compatible via STORAGE_BACKEND=s3.
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from app.services.storage_backends import get_storage_backend
from app.services.storage_backends.base import DocumentStorageError
from app.services.storage_backends.local import LocalStorageBackend


class InvalidPdfError(ValueError):
    """Raised when uploaded content is not a PDF."""


def _resolve_storage_root(config: Mapping[str, Any] | None = None) -> Path:
    backend = get_storage_backend(config)
    if isinstance(backend, LocalStorageBackend):
        return backend.root
    from app.services.storage_backends.base import resolve_storage_config

    resolved = resolve_storage_config(config)
    root = str(resolved.get('DOCUMENT_STORAGE_PATH', 'data/guides') or 'data/guides')
    return Path(root)


def build_storage_path(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> str:
    """Return logical storage path stored in guide_documents.storage_path."""
    return get_storage_backend(config).build_storage_path(doc_id)


def document_dir(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> Path:
    """Absolute path to the document directory (local backend only)."""
    backend = get_storage_backend(config)
    if isinstance(backend, LocalStorageBackend):
        return backend.document_dir(doc_id)
    return _resolve_storage_root(config) / str(doc_id)


def original_file_path(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> Path:
    """Absolute path to original.pdf (local backend; S3 returns expected local-style path)."""
    backend = get_storage_backend(config)
    if isinstance(backend, LocalStorageBackend):
        return backend.original_file_path(doc_id)
    return document_dir(doc_id, config=config) / 'original.pdf'


def validate_pdf(data: bytes, content_type: str | None = None) -> None:
    """Validate PDF magic bytes and optional MIME type."""
    if not data:
        raise InvalidPdfError('file is empty')

    if not data.startswith(b'%PDF'):
        raise InvalidPdfError('file is not a PDF')

    mime = str(content_type or '').strip().lower()
    if mime and 'pdf' not in mime:
        raise InvalidPdfError('file must have PDF content type')


def save_original(
    doc_id: str | uuid.UUID,
    data: bytes,
    *,
    config: Mapping[str, Any] | None = None,
) -> Path:
    """Write original.pdf via configured backend."""
    backend = get_storage_backend(config)
    backend.save_original(doc_id, data)
    if isinstance(backend, LocalStorageBackend):
        return backend.original_file_path(doc_id)
    return original_file_path(doc_id, config=config)


def delete_document_dir(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> None:
    """Remove stored original (local directory or S3 object)."""
    purge_document_storage(doc_id, config=config)


def purge_document_storage(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> None:
    """Remove stored original PDF for a document."""
    get_storage_backend(config).purge(doc_id)


def original_exists(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> bool:
    """Return True when original PDF exists in configured backend."""
    return get_storage_backend(config).exists(doc_id)


@contextmanager
def materialize_original(
    doc_id: str | uuid.UUID,
    *,
    config: Mapping[str, Any] | None = None,
) -> Iterator[Path | None]:
    """Yield filesystem Path for PyMuPDF; None when original is missing."""
    with get_storage_backend(config).materialize_original(doc_id) as path:
        yield path


__all__ = [
    'DocumentStorageError',
    'InvalidPdfError',
    'build_storage_path',
    'document_dir',
    'original_file_path',
    'validate_pdf',
    'save_original',
    'delete_document_dir',
    'purge_document_storage',
    'original_exists',
    'materialize_original',
]
