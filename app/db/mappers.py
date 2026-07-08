"""Map database rows to normalized catalog card JSON."""
from __future__ import annotations


def row_to_card(row: dict, content_type: str) -> dict:
    """
    Map a DB row to a catalog card (tecnic §6.13).

    Target fields: id, type, title, location, description, url, image, date,
    entity_id. Fase 3 will also add source_type and source_id for future RAG
    (see docs/devs/preparacio-rag-cataleg.md).

    Args:
        row: Raw row dict from a repository query.
        content_type: Domain discriminator (establishment, article, event, …).

    Returns:
        Normalized card dict for results[].

    Raises:
        NotImplementedError: Skeleton only; implemented per repository in Fase 3.
    """
    raise NotImplementedError(
        f'row_to_card is not implemented for content_type={content_type!r} (Fase 3)'
    )
