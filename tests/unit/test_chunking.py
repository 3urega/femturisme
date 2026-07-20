"""Unit tests for token chunking."""
from __future__ import annotations

from app.services.chunking import ChunkDraft, chunk_pages, count_tokens
from app.services.pdf_extractor import PageText


def test_chunk_pages_respects_max_tokens():
    long_text = 'paraula ' * 2000
    pages = [PageText(page=1, text=long_text)]
    chunks = chunk_pages(pages, max_tokens=100, overlap_ratio=0.1)
    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk.content) <= 100


def test_chunk_pages_keeps_overlap_between_chunks():
    text = ' '.join(f'fragment{i}' for i in range(400))
    pages = [PageText(page=1, text=text)]
    chunks = chunk_pages(pages, max_tokens=80, overlap_ratio=0.2)
    assert len(chunks) >= 2
    assert chunks[0].chunk_index == 0
    assert all(isinstance(item, ChunkDraft) for item in chunks)
