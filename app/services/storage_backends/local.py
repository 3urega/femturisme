"""Local filesystem storage backend for guide PDFs."""
from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from app.services.storage_backends.base import DocumentStorageError, StorageBackend
    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        root = 'data/guides'
        if config is not None:
            root = str(config.get('DOCUMENT_STORAGE_PATH', root) or root)
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def build_storage_path(self, doc_id: str | uuid.UUID) -> str:
        normalized_root = str(self._root).replace('\\', '/').rstrip('/')
        return f'{normalized_root}/{doc_id}/original.pdf'

    def document_dir(self, doc_id: str | uuid.UUID) -> Path:
        return self._root / str(doc_id)

    def original_file_path(self, doc_id: str | uuid.UUID) -> Path:
        return self.document_dir(doc_id) / 'original.pdf'

    def save_original(self, doc_id: str | uuid.UUID, data: bytes) -> str:
        target = self.original_file_path(doc_id)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as exc:
            raise DocumentStorageError(str(exc)) from exc
        return self.build_storage_path(doc_id)

    def exists(self, doc_id: str | uuid.UUID) -> bool:
        return self.original_file_path(doc_id).is_file()

    def purge(self, doc_id: str | uuid.UUID) -> None:
        directory = self.document_dir(doc_id)
        if not directory.exists():
            return
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            raise DocumentStorageError(str(exc)) from exc

    @contextmanager
    def _materialize_original_path(self, doc_id: str | uuid.UUID) -> Iterator[Path]:
        yield self.original_file_path(doc_id)
