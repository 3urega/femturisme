"""MySQL repository for promotional experiences (ofertes)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards

_SEARCH_SQL = """
SELECT
    og.id,
    oc.titol AS title,
    oc.param_url,
    oc.resum AS description,
    og.imatge AS image,
    og.preu_oferta,
    eg.nom AS establishment_name,
    pg.poble AS location,
    pc.comarca,
    gco.categoria_ca AS category
FROM oferta_general og
INNER JOIN oferta_continguts oc
    ON oc.id_oferta = og.id AND oc.idioma = %s
LEFT JOIN establiment_general eg ON eg.id = og.id_establiment
LEFT JOIN poble_general pg ON pg.id = COALESCE(NULLIF(og.id_poble, 0), eg.id_poble)
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
LEFT JOIN oferta_categories ocat ON ocat.id_oferta = og.id
LEFT JOIN generic_categoria_oferta gco ON gco.id = ocat.id_categoria
WHERE og.estat <> 'borrador'
  AND og.data_inicial <= NOW()
  AND (og.data_final IS NULL OR og.data_final < '1000-01-01' OR og.data_final >= NOW())
  AND (
      pg.poble LIKE %s
      OR pc.comarca LIKE %s
  )
  AND (%s IS NULL OR gco.categoria_ca LIKE %s)
  AND (%s IS NULL OR eg.nom LIKE %s)
GROUP BY og.id, oc.titol, oc.param_url, oc.resum, og.imatge, og.preu_oferta,
         og.data_inicial, eg.nom, pg.poble, pc.comarca, gco.categoria_ca
ORDER BY og.data_inicial DESC
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
    category: str | None = None,
    establishment: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search promotional experiences and offers by destination and optional filters.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern = f'%{destination}%'

    category_text = (category or '').strip() or None
    establishment_text = (establishment or '').strip() or None
    category_pattern = _optional_pattern(category_text)
    establishment_pattern = _optional_pattern(establishment_text)

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        category_pattern,
        category_pattern,
        establishment_pattern,
        establishment_pattern,
        row_limit,
    )

    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(_SEARCH_SQL, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'experience')
    return build_search_wrapper(
        destination=destination,
        results=cards,
        total=str(len(cards)),
        category=category_text,
        establishment=establishment_text,
        lang=lang,
    )
