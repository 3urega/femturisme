"""Unit tests for indexing pipeline doc_id lock (issue #34)."""
from __future__ import annotations

import threading
import time
import uuid
from unittest.mock import patch

from app.services.indexing_pipeline import schedule_indexing


def test_concurrent_schedule_indexing_runs_once():
    doc_id = uuid.uuid4()
    runs: list[str] = []
    run_lock = threading.Lock()
    started = threading.Event()

    def fake_run_indexing(inner_doc_id, **kwargs):
        with run_lock:
            runs.append(str(inner_doc_id))
        started.set()
        time.sleep(0.4)

    config = {'DOCUMENT_STORAGE_PATH': 'data/guides'}

    with patch('app.services.indexing_pipeline._run_indexing', side_effect=fake_run_indexing):
        schedule_indexing(doc_id, config=config)
        schedule_indexing(doc_id, config=config)

        assert started.wait(timeout=2), 'expected first indexing thread to start'
        time.sleep(0.8)

    assert len(runs) == 1
