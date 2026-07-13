"""MySQL repository for catalog establishments (sleep + dining)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards

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
WHERE eg.actiu = 1
  AND (eg.data_baixa IS NULL OR eg.data_baixa < '1000-01-01')
  AND eg.sense_fitxa = 0
  AND (
      pg.poble LIKE %s
      OR pc.comarca LIKE %s
      OR pg2.poble LIKE %s
      OR pc2.comarca LIKE %s
  )
  AND (%s IS NULL OR gte.code = %s OR gte.tipus_ca LIKE %s)
GROUP BY eg.id, eg.nom, eg.param_url, eg.imatge
ORDER BY eg.nom
LIMIT %s
"""


def search(
    *,
    destination: str,
    type: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search establishments by destination and optional type.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern = f'%{destination}%'

    type_code: str | None = None
    type_pattern: str | None = None
    if type:
        normalized = type.strip().lower()
        if normalized:
            type_code = normalized
            type_pattern = f'%{normalized}%'

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        type_code,
        type_code,
        type_pattern,
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
        type=type,
        lang=lang,
    )
