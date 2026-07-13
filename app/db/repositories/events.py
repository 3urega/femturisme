"""MySQL repository for calendar events (agenda)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards

_SEARCH_SQL = """
SELECT
    ag.id,
    ac.titol AS title,
    ac.param_url,
    ac.descripcio AS description,
    ag.imatge AS image,
    MIN(ad.data_inici) AS date_start,
    MAX(ad.data_final) AS date_end,
    pg.poble AS location,
    pc.comarca
FROM agenda_general ag
INNER JOIN agenda_continguts ac
    ON ac.id_agenda = ag.id AND ac.idioma = %s
INNER JOIN agenda_dates ad ON ad.id_agenda = ag.id
LEFT JOIN agenda_pobles ap ON ap.id_agenda = ag.id
LEFT JOIN poble_general pg ON pg.id = ap.id_poble
LEFT JOIN poble_comarques pc ON pc.id = pg.id_comarca
WHERE ag.activa = 1
  AND ag.baixa = 0
  AND ag.arxivada = 0
  AND (
      pg.poble LIKE %s
      OR pc.comarca LIKE %s
  )
  AND (%s IS NULL OR ad.data_final >= %s)
  AND (%s IS NULL OR ad.data_inici <= %s)
GROUP BY ag.id, ac.titol, ac.param_url, ac.descripcio, ag.imatge, pg.poble, pc.comarca
ORDER BY date_start
LIMIT %s
"""


def _normalize_date(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def search(
    *,
    destination: str,
    date_from: str | None = None,
    date_to: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search calendar events by destination and optional date range.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination = destination.strip()
    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    destination_pattern = f'%{destination}%'
    date_from = _normalize_date(date_from)
    date_to = _normalize_date(date_to)

    params = (
        lang,
        destination_pattern,
        destination_pattern,
        date_from,
        date_from,
        date_to,
        date_to,
        row_limit,
    )

    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(_SEARCH_SQL, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'event')
    return build_search_wrapper(
        destination=destination,
        results=cards,
        total=str(len(cards)),
        date_from=date_from,
        date_to=date_to,
        lang=lang,
    )
