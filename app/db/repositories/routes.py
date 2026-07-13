"""MySQL repository for tourist routes (rutes)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards

_SEARCH_SQL = """
SELECT
    rg.id,
    rc.titol AS title,
    rc.param_url,
    rc.introduccio AS description,
    rg.imatge AS image,
    gt.tematica_ca AS route_type,
    pg.poble AS location,
    pc.comarca
FROM ruta_general rg
INNER JOIN ruta_continguts rc
    ON rc.id_ruta = rg.id AND rc.idioma = %s
LEFT JOIN ruta_pobles rp ON rp.id_ruta = rg.id
LEFT JOIN poble_general pg ON pg.id = rp.id_poble
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
LEFT JOIN ruta_tematica rt ON rt.id_ruta = rg.id
LEFT JOIN generic_tematiques gt ON gt.id = rt.id_tematica
WHERE rg.actiu = 1
  AND (
      pg.poble LIKE %s
      OR pc.comarca LIKE %s
  )
  AND (%s IS NULL OR gt.tematica_ca LIKE %s OR gt.code LIKE %s)
GROUP BY rg.id, rc.titol, rc.param_url, rc.introduccio, rg.imatge,
         gt.tematica_ca, pg.poble, pc.comarca
ORDER BY rc.titol
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
    lang: str = 'ca',
    limit: int = 20,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search tourist routes by destination and optional modality type.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern = f'%{destination}%'

    type_text = (type or '').strip() or None
    type_pattern = _optional_pattern(type_text)

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        type_pattern,
        type_pattern,
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

    cards = rows_to_cards(rows, 'route')
    return build_search_wrapper(
        destination=destination,
        results=cards,
        total=str(len(cards)),
        type=type_text,
        lang=lang,
    )
