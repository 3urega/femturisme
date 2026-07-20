"""MySQL repository for calendar events (agenda)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.mappers import build_search_wrapper, rows_to_cards
from app.db.territory import location_predicate, resolve_geo_filter

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
  AND {location_filter}
  AND (%s IS NULL OR ad.data_final >= %s)
  AND (%s IS NULL OR ad.data_inici <= %s)
  AND (%s IS NULL OR ac.titol LIKE %s OR ac.descripcio LIKE %s)
GROUP BY ag.id, ac.titol, ac.param_url, ac.descripcio, ag.imatge, pg.poble, pc.comarca
ORDER BY date_start
LIMIT %s
"""


def _optional_pattern(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return f'%{text}%'


def _normalize_date(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def search(
    *,
    destination: str | None = None,
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    skip_location_filter: bool = False,
    retried: bool = False,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search calendar events by destination, free-text query, and optional date range.

    At least one of destination or query is required.

    Returns the catalog search wrapper (destination, total, results[], error).
    """
    destination_text = (destination or '').strip() or None
    query_text = (query or '').strip() or None

    if not destination_text and not query_text:
        return build_search_wrapper(
            destination='',
            results=[],
            total='0',
            error='At least one of destination or query is required',
        )

    lang = (lang or 'ca').strip()
    row_limit = max(1, min(int(limit), 20))
    effective_skip_location = skip_location_filter or not destination_text
    geo = resolve_geo_filter(
        destination_text or '',
        skip_location_filter=effective_skip_location,
        config=config,
    )
    location_filter, location_params = location_predicate(geo)
    date_from = _normalize_date(date_from)
    date_to = _normalize_date(date_to)
    query_pattern = _optional_pattern(query_text)

    params = (
        lang,
        *location_params,
        date_from,
        date_from,
        date_to,
        date_to,
        query_pattern,
        query_pattern,
        query_pattern,
        row_limit,
    )

    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                _SEARCH_SQL.format(location_filter=location_filter),
                params,
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'event')
    return build_search_wrapper(
        destination=destination_text or '',
        results=cards,
        total=str(len(cards)),
        location_filter_applied=geo.location_filter_applied,
        retried=retried,
        date_from=date_from,
        date_to=date_to,
        lang=lang,
        query=query_text,
        **geo.meta_extras(),
    )
