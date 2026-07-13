"""MySQL repository for articles and news (notícies)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards

_SEARCH_SQL = """
SELECT
    ng.id,
    nc.titol AS title,
    nc.param_url,
    ng.data AS published_at,
    ng.imatge AS image,
    LEFT(nc.cos, 300) AS description,
    pg.poble AS location,
    pc.comarca
FROM noticia_general ng
INNER JOIN noticia_continguts nc
    ON nc.id_noticia = ng.id AND nc.idioma = %s
LEFT JOIN noticia_pobles np ON np.id_noticia = ng.id
LEFT JOIN poble_general pg ON pg.id = np.id_poble
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
WHERE ng.actiu = 1
  AND (ng.permanent = 1 OR ng.data_caducitat >= CURDATE())
  AND (%s IS NULL OR pg.poble LIKE %s OR pc.comarca LIKE %s)
  AND (%s IS NULL OR nc.titol LIKE %s OR nc.cos LIKE %s)
  AND (%s IS NULL OR nc.titol LIKE %s OR nc.cos LIKE %s)
GROUP BY ng.id, nc.titol, nc.param_url, ng.data, ng.imatge, nc.cos, pg.poble, pc.comarca
ORDER BY ng.data DESC
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
    destination: str | None = None,
    topic: str | None = None,
    query: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search editorial articles and news by territory, topic or free text.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))

    destination_text = (destination or '').strip() or None
    topic_text = (topic or '').strip() or None
    query_text = (query or '').strip() or None

    destination_pattern = _optional_pattern(destination_text)
    topic_pattern = _optional_pattern(topic_text)
    query_pattern = _optional_pattern(query_text)

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        destination_pattern,
        topic_pattern,
        topic_pattern,
        topic_pattern,
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

    cards = rows_to_cards(rows, 'article')
    return build_search_wrapper(
        destination=destination_text or '',
        results=cards,
        total=str(len(cards)),
        topic=topic_text,
        query=query_text,
        lang=lang,
    )
