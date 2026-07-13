"""MySQL repository for catalog establishments (sleep + dining)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards
from app.db.territory import resolve_location_filter

_SEARCH_SQL = """
SELECT
    eg.id,
    eg.nom AS title,
    eg.param_url,
    eg.imatge AS image,
    ANY_VALUE(gte.code) AS type_code,
    ANY_VALUE(gte.tipus_ca) AS type_label,
    ANY_VALUE(pg.poble) AS location,
    ANY_VALUE(pc.comarca) AS comarca,
    ANY_VALUE(ec.description) AS description
FROM establiment_general eg
INNER JOIN establiment_continguts ec
    ON ec.id_establiment = eg.id AND ec.idioma = %s
LEFT JOIN establiment_tipus et ON et.id_establiment = eg.id
LEFT JOIN generic_tipus_establiment gte ON gte.id = et.id_tipus
LEFT JOIN poble_general pg ON pg.id = eg.id_poble
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
LEFT JOIN establiment_pobles ep ON ep.id_establiment = eg.id
LEFT JOIN poble_general pg2 ON pg2.id = ep.id_poble
LEFT JOIN poble_comarques pc2 ON pc2.id = pg2.id_comarca
WHERE (eg.data_baixa IS NULL OR eg.data_baixa < '1000-01-01')
  AND eg.sense_fitxa = 0
  AND (
      %s IS NULL
      OR pg.poble LIKE %s
      OR pc.comarca LIKE %s
      OR pg2.poble LIKE %s
      OR pc2.comarca LIKE %s
  )
  AND (%s IS NULL OR gte.code LIKE %s OR gte.tipus_ca LIKE %s)
  AND (
      %s IS NULL
      OR eg.nom LIKE %s
      OR ec.description LIKE %s
      OR ec.introduccio LIKE %s
      OR ec.contingut LIKE %s
      OR ec.keywords LIKE %s
  )
GROUP BY eg.id, eg.nom, eg.param_url, eg.imatge
ORDER BY eg.nom
LIMIT %s
"""


def _optional_pattern(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f'%{text}%'


def search(
    *,
    destination: str,
    type: str | None = None,
    query: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    skip_location_filter: bool = False,
    retried: bool = False,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search establishments by destination, optional type and optional free text.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern, location_filter_applied = resolve_location_filter(
        destination,
        skip_location_filter=skip_location_filter,
    )

    type_pattern: str | None = None
    if type:
        normalized = type.strip().lower()
        if normalized:
            type_pattern = f'%{normalized}%'

    query_text = (query or '').strip() or None
    query_pattern = _optional_pattern(query_text)

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        type_pattern,
        type_pattern,
        type_pattern,
        query_pattern,
        query_pattern,
        query_pattern,
        query_pattern,
        query_pattern,
        query_pattern,
        row_limit,
    )

    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(_SEARCH_SQL, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'establishment')
    return build_search_wrapper(
        destination=destination,
        results=cards,
        total=str(len(cards)),
        location_filter_applied=location_filter_applied,
        retried=retried,
        type=type,
        query=query_text,
        lang=lang,
    )
