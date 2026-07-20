"""PDF indexing pipeline: extract → chunk → embed → pgvector."""
from __future__ import annotations

import logging
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Mapping

from app.config import Config
from app.db.repositories import document_chunks as chunks_repo
from app.db.repositories import documents as documents_repo
from app.services.chunking import chunk_pages
from app.services.document_storage import original_file_path
from app.services.embedding_service import EmbeddingService
from app.services.pdf_extractor import PdfExtractionError, extract_pages

logger = logging.getLogger(__name__)

_INDEXING_CONFIG_KEYS = (
    'POSTGRES_HOST',
    'POSTGRES_PORT',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DATABASE',
    'POSTGRES_CONNECT_TIMEOUT',
    'POSTGRES_SSLMODE',
    'DOCUMENT_STORAGE_PATH',
    'OPENAI_API_KEY',
    'EMBEDDING_MODEL',
)


class IndexingPipelineError(Exception):
    """Raised when indexing cannot proceed."""


_INDEXING_GUARD = threading.Lock()
_DOC_LOCKS: dict[str, threading.Lock] = {}


@contextmanager
def _doc_indexing_lock(doc_id: str | uuid.UUID) -> Iterator[bool]:
    doc_key = str(doc_id)
    with _INDEXING_GUARD:
        lock = _DOC_LOCKS.setdefault(doc_key, threading.Lock())
    acquired = lock.acquire(blocking=False)
    if not acquired:
        logger.warning('indexing already in progress for doc_id=%s', doc_key)
        yield False
        return
    try:
        yield True
    finally:
        lock.release()


def _resolve_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    if config is not None:
        return dict(config)
    try:
        from flask import current_app

        return {key: current_app.config.get(key) for key in _INDEXING_CONFIG_KEYS}
    except RuntimeError:
        return {key: getattr(Config, key) for key in _INDEXING_CONFIG_KEYS}


def _log_step(
    *,
    doc_id: str,
    step: str,
    started: float,
    chunks_ok: int = 0,
    chunks_ko: int = 0,
    extra: Mapping[str, Any] | None = None,
) -> None:
    payload = {
        'doc_id': doc_id,
        'step': step,
        'duration_ms': int((time.perf_counter() - started) * 1000),
        'chunks_ok': chunks_ok,
        'chunks_ko': chunks_ko,
    }
    if extra:
        payload.update(dict(extra))
    logger.info('indexing step', extra=payload)


def _mark_failed(
    doc_id: str | uuid.UUID,
    message: str,
    *,
    config: Mapping[str, Any] | None,
) -> None:
    documents_repo.update_indexing_state(
        doc_id,
        'failed',
        error_message=message,
        config=config,
    )


def run(
    doc_id: str | uuid.UUID,
    *,
    reindex: bool = False,
    config: Mapping[str, Any] | None = None,
    embedder: Callable[[list[str], str | None], list[list[float]]] | None = None,
) -> None:
    """Run the full indexing pipeline for one document."""
    with _doc_indexing_lock(doc_id) as acquired:
        if not acquired:
            return
        _run_indexing(doc_id, reindex=reindex, config=config, embedder=embedder)


def _run_indexing(
    doc_id: str | uuid.UUID,
    *,
    reindex: bool = False,
    config: Mapping[str, Any] | None = None,
    embedder: Callable[[list[str], str | None], list[list[float]]] | None = None,
) -> None:
    cfg = _resolve_config(config)
    doc_id_str = str(doc_id)
    started_total = time.perf_counter()

    document = documents_repo.get_raw_by_id(doc_id, config=cfg)
    if document is None:
        raise IndexingPipelineError(f'document not found: {doc_id_str}')

    if reindex:
        step_started = time.perf_counter()
        chunks_repo.delete_by_doc_id(doc_id, config=cfg)
        updated = documents_repo.prepare_reindex(doc_id, config=cfg)
        if updated is None:
            raise IndexingPipelineError(f'document not found for reindex: {doc_id_str}')
        document = documents_repo.get_raw_by_id(doc_id, config=cfg)
        _log_step(doc_id=doc_id_str, step='reindex_reset', started=step_started)

    pdf_path = original_file_path(doc_id, config=cfg)
    if not pdf_path.is_file():
        message = f'PDF file not found: {pdf_path}'
        _mark_failed(doc_id, message, config=cfg)
        raise IndexingPipelineError(message)

    try:
        step_started = time.perf_counter()
        documents_repo.update_indexing_state(
            doc_id,
            'extracting',
            clear_error=True,
            config=cfg,
        )
        pages = extract_pages(pdf_path)
        if not pages:
            raise IndexingPipelineError('PDF contains no extractable text')
        _log_step(
            doc_id=doc_id_str,
            step='extracting',
            started=step_started,
            chunks_ok=len(pages),
        )

        step_started = time.perf_counter()
        documents_repo.update_indexing_state(doc_id, 'chunking', config=cfg)
        chunks = chunk_pages(pages)
        if not chunks:
            raise IndexingPipelineError('chunking produced no fragments')
        _log_step(
            doc_id=doc_id_str,
            step='chunking',
            started=step_started,
            chunks_ok=len(chunks),
        )

        step_started = time.perf_counter()
        documents_repo.update_indexing_state(
            doc_id,
            'embedding',
            pages_count=len(pages),
            chunks_count=len(chunks),
            embedded_chunks_count=0,
            config=cfg,
        )
        embedding_model = str(cfg.get('EMBEDDING_MODEL') or Config.EMBEDDING_MODEL)
        service = EmbeddingService(config=cfg, embedder=embedder)
        embeddings = service.embed_texts([chunk.content for chunk in chunks], embedding_model)
        _log_step(
            doc_id=doc_id_str,
            step='embedding',
            started=step_started,
            chunks_ok=len(embeddings),
        )

        indexed_at = datetime.now(timezone.utc)
        metadata_base = {
            'doc_title': document.get('title'),
            'source_file': document.get('source_filename'),
            'embedding_model': embedding_model,
            'indexed_at': indexed_at.isoformat(),
        }

        step_started = time.perf_counter()
        inserted = chunks_repo.insert_batch(
            doc_id=doc_id,
            entity_id=document['entity_id'],
            category=document.get('category'),
            chunks=chunks,
            embeddings=embeddings,
            metadata_base=metadata_base,
            config=cfg,
        )
        if inserted != len(chunks):
            raise IndexingPipelineError(
                f'expected to insert {len(chunks)} chunks, inserted {inserted}'
            )

        documents_repo.update_indexing_state(
            doc_id,
            'indexed',
            pages_count=len(pages),
            chunks_count=len(chunks),
            embedded_chunks_count=len(embeddings),
            embedding_model=embedding_model,
            indexed_at=indexed_at,
            clear_error=True,
            config=cfg,
        )
        _log_step(
            doc_id=doc_id_str,
            step='indexed',
            started=step_started,
            chunks_ok=inserted,
        )
        _log_step(
            doc_id=doc_id_str,
            step='complete',
            started=started_total,
            chunks_ok=inserted,
        )
    except (PdfExtractionError, IndexingPipelineError, Exception) as exc:
        _mark_failed(doc_id, str(exc), config=cfg)
        _log_step(
            doc_id=doc_id_str,
            step='failed',
            started=started_total,
            chunks_ko=1,
            extra={'error': str(exc)[:500]},
        )
        raise


def schedule_indexing(
    doc_id: str | uuid.UUID,
    *,
    reindex: bool = False,
    config: Mapping[str, Any] | None = None,
    embedder: Callable[[list[str], str | None], list[list[float]]] | None = None,
) -> None:
    """Run indexing in a background daemon thread."""
    doc_key = str(doc_id)
    with _INDEXING_GUARD:
        lock = _DOC_LOCKS.setdefault(doc_key, threading.Lock())
        if lock.locked():
            logger.warning('skip concurrent schedule_indexing for doc_id=%s', doc_key)
            return

    cfg = _resolve_config(config)

    def _target() -> None:
        try:
            run(doc_id, reindex=reindex, config=cfg, embedder=embedder)
        except Exception:
            logger.exception('background indexing failed for doc_id=%s', doc_id)

    thread = threading.Thread(
        target=_target,
        name=f'indexing-{doc_id}',
        daemon=True,
    )
    thread.start()
