"""Filesystem storage for uploaded guide PDFs (DEV-503).

Backend: local disc via DOCUMENT_STORAGE_PATH (default).
Planned: Supabase S3 when STORAGE_BACKEND=s3 — see issue #35.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping

from app.config import Config


class InvalidPdfError(ValueError):
    """Raised when uploaded content is not a PDF."""


class DocumentStorageError(OSError):
    """Raised when file storage operations fail."""


def _resolve_storage_root(config: Mapping[str, Any] | None = None) -> Path:
    if config is not None:
        root = str(config.get('DOCUMENT_STORAGE_PATH', 'data/guides') or 'data/guides')
        return Path(root)

    try:
        from flask import current_app

        root = str(current_app.config.get('DOCUMENT_STORAGE_PATH', 'data/guides') or 'data/guides')
        return Path(root)
    except RuntimeError:
        return Path(getattr(Config, 'DOCUMENT_STORAGE_PATH', 'data/guides'))


def build_storage_path(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> str:
    """Return relative storage path stored in guide_documents.storage_path."""
    root = _resolve_storage_root(config)
    normalized_root = str(root).replace('\\', '/').rstrip('/')
    return f'{normalized_root}/{doc_id}/original.pdf'


def document_dir(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> Path:
    """Absolute path to the document directory."""
    return _resolve_storage_root(config) / str(doc_id)


def original_file_path(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> Path:
    """Absolute path to original.pdf for a document."""
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
    """Write original.pdf under the document directory."""
    target = original_file_path(doc_id, config=config)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    except OSError as exc:
        raise DocumentStorageError(str(exc)) from exc
    return target


def delete_document_dir(doc_id: str | uuid.UUID, *, config: Mapping[str, Any] | None = None) -> None:
    """Remove the document directory from disk if it exists."""
    directory = document_dir(doc_id, config=config)
    if not directory.exists():
        return
    try:
        shutil.rmtree(directory)
    except OSError as exc:
        raise DocumentStorageError(str(exc)) from exc
