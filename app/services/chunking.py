"""Token-based text chunking for RAG indexing."""
from __future__ import annotations

from dataclasses import dataclass

import tiktoken

DEFAULT_ENCODING = 'cl100k_base'
DEFAULT_MAX_TOKENS = 800
DEFAULT_OVERLAP_RATIO = 0.12


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    page: int | None
    content: str


def _get_encoding(name: str = DEFAULT_ENCODING):
    return tiktoken.get_encoding(name)


def count_tokens(text: str, *, encoding_name: str = DEFAULT_ENCODING) -> int:
    encoding = _get_encoding(encoding_name)
    return len(encoding.encode(text))


def chunk_pages(
    pages: list,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_ratio: float = DEFAULT_OVERLAP_RATIO,
    encoding_name: str = DEFAULT_ENCODING,
) -> list[ChunkDraft]:
    """
    Split page texts into overlapping chunks within the 500-1000 token range.

    Pages are expected to expose `.page` and `.text` attributes.
    """
    if max_tokens < 1:
        raise ValueError('max_tokens must be >= 1')

    encoding = _get_encoding(encoding_name)
    overlap_tokens = max(1, int(max_tokens * overlap_ratio))
    chunks: list[ChunkDraft] = []
    chunk_index = 0

    for page in pages:
        page_number = getattr(page, 'page', None)
        text = str(getattr(page, 'text', page) or '').strip()
        if not text:
            continue

        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            chunks.append(ChunkDraft(chunk_index=chunk_index, page=page_number, content=text))
            chunk_index += 1
            continue

        start = 0
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            piece = encoding.decode(tokens[start:end]).strip()
            if piece:
                chunks.append(ChunkDraft(chunk_index=chunk_index, page=page_number, content=piece))
                chunk_index += 1
            if end >= len(tokens):
                break
            start = max(end - overlap_tokens, start + 1)

    return chunks
