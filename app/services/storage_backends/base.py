"""Storage backend abstraction for guide PDF originals (issue #35)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping


class DocumentStorageError(OSError):
    """Raised when storage operations fail."""


class StorageBackend(ABC):
    """Backend for original.pdf storage (local disc or S3-compatible)."""

    @abstractmethod
    def build_storage_path(self, doc_id: str | uuid.UUID) -> str:
        """Return logical storage path stored in guide_documents.storage_path."""

    @abstractmethod
    def save_original(self, doc_id: str | uuid.UUID, data: bytes) -> str:
        """Persist PDF bytes; return logical storage path."""

    @abstractmethod
    def exists(self, doc_id: str | uuid.UUID) -> bool:
        """Return True when original PDF is stored."""

    @abstractmethod
    def purge(self, doc_id: str | uuid.UUID) -> None:
        """Remove stored original PDF if present."""

    @contextmanager
    def materialize_original(self, doc_id: str | uuid.UUID) -> Iterator[Path | None]:
        """Yield a filesystem Path suitable for PyMuPDF extraction."""
        if not self.exists(doc_id):
            yield None
            return
        with self._materialize_original_path(doc_id) as path:
            yield path

    @contextmanager
    def _materialize_original_path(self, doc_id: str | uuid.UUID) -> Iterator[Path]:
        """Subclass hook: yield Path; local uses real file, S3 uses tempfile."""
        raise NotImplementedError


STORAGE_CONFIG_KEYS = (
    'STORAGE_BACKEND',
    'DOCUMENT_STORAGE_PATH',
    'S3_ENDPOINT',
    'S3_REGION',
    'S3_BUCKET',
    'S3_ACCESS_KEY_ID',
    'S3_SECRET_ACCESS_KEY',
)


def resolve_storage_config(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if config is not None:
        return {key: config.get(key) for key in STORAGE_CONFIG_KEYS}
    try:
        from flask import current_app

        return {key: current_app.config.get(key) for key in STORAGE_CONFIG_KEYS}
    except RuntimeError:
        from app.config import Config

        return {key: getattr(Config, key, None) for key in STORAGE_CONFIG_KEYS}
