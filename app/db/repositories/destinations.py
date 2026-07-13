"""MySQL repository for destinations (on anar — towns and places)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards
from app.db.territory import resolve_location_filter

_SEARCH_SQL = """
SELECT
    pg.id,
    pg.poble AS title,
    pg.param_url,
    pg.imatge AS image,
    pc.comarca AS region,
    pcont.description AS description
FROM poble_general pg
LEFT JOIN poble_continguts pcont
    ON pcont.id_poble = pg.id AND pcont.idioma = %s
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
WHERE pg.poble <> ''
  AND (
      %s IS NULL
      OR pg.poble LIKE %s
      OR pg.param_url LIKE %s
      OR pc.comarca LIKE %s
  )
  AND (%s IS NULL OR pc.comarca LIKE %s)
ORDER BY pg.poble
LIMIT %s
"""


def search(
    *,
    destination: str,
    region: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    skip_location_filter: bool = False,
    retried: bool = False,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search towns and places to visit by destination and optional region.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern, location_filter_applied = resolve_location_filter(
        destination,
        skip_location_filter=skip_location_filter,
    )

    region_pattern: str | None = None
    if region:
        normalized = region.strip()
        if normalized:
            region_pattern = f'%{normalized}%'

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        region_pattern,
        region_pattern,
        row_limit,
    )

    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(_SEARCH_SQL, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'destination')
    return build_search_wrapper(
        destination=destination,
        results=cards,
        total=str(len(cards)),
        location_filter_applied=location_filter_applied,
        retried=retried,
        region=region,
        lang=lang,
    )
