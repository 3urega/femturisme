"""PDF text extraction for the RAG indexing pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class PdfExtractionError(Exception):
    """Raised when a PDF cannot be read or parsed."""


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


def extract_pages(pdf_path: Path) -> list[PageText]:
    """Extract non-empty text per page from a PDF file."""
    path = Path(pdf_path)
    if not path.is_file():
        raise PdfExtractionError(f'PDF file not found: {path}')

    try:
        import fitz
    except ImportError as exc:
        raise PdfExtractionError('pymupdf is not installed') from exc

    pages: list[PageText] = []
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PdfExtractionError(f'failed to open PDF: {exc}') from exc

    try:
        for index in range(document.page_count):
            page = document.load_page(index)
            text = (page.get_text('text') or '').strip()
            if text:
                pages.append(PageText(page=index + 1, text=text))
    except Exception as exc:
        raise PdfExtractionError(f'failed to extract PDF text: {exc}') from exc
    finally:
        document.close()

    return pages
