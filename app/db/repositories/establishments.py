"""MySQL repository for catalog establishments (sleep + dining)."""
from __future__ import annotations

from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.geo_radius import (
    OriginPoint,
    build_radius_filter,
    resolve_origin_coordinates,
)
from app.db.mappers import build_search_meta, build_search_wrapper, rows_to_cards
from app.db.territory import location_predicate, resolve_geo_filter

_LAT_EXPR = "COALESCE(NULLIF(eg.latitud, ''), pg.latitud)"
_LNG_EXPR = "COALESCE(NULLIF(eg.longitud, ''), pg.longitud)"

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
  AND {location_filter}
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


def _origin_to_meta(origin: OriginPoint) -> dict[str, object]:
    return {
        'lat': origin.lat,
        'lng': origin.lng,
        'label': origin.label,
        'source': origin.source,
    }


def _build_radius_meta(
    *,
    origin: OriginPoint,
    distance_km: float,
    results: list[dict],
) -> dict[str, Any]:
    return {
        'scope': 'radius',
        'location_filter_applied': True,
        'distance_km': distance_km,
        'origin': _origin_to_meta(origin),
        'hint': None,
        'truncated': len(results) > 0 and len(results) >= 20,
    }


def _territorial_location_predicate(geo):
    return location_predicate(
        geo,
        extra_poble_id_cols=('pg2.id',),
        extra_like_pairs=(('pg2.poble', 'pc2.comarca'),),
    )


def search(
    *,
    destination: str,
    type: str | None = None,
    query: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    distance_km: float | int | None = None,
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

    radius_km: float | None = None
    if distance_km is not None:
        try:
            parsed_km = float(distance_km)
            if parsed_km > 0:
                radius_km = parsed_km
        except (TypeError, ValueError):
            radius_km = None

    custom_meta: dict[str, Any] | None = None
    resolved_origin: OriginPoint | None = None
    geo = resolve_geo_filter(
        destination,
        skip_location_filter=skip_location_filter,
        config=config,
    )

    if radius_km is not None:
        resolved_origin = resolve_origin_coordinates(destination, config=config)
        if resolved_origin is not None:
            location_filter, location_params = build_radius_filter(
                resolved_origin,
                lat_expr=_LAT_EXPR,
                lng_expr=_LNG_EXPR,
                max_km=radius_km,
            )
        else:
            location_filter, location_params = _territorial_location_predicate(geo)
            zone_meta = geo.meta_extras()
            custom_meta = build_search_meta(
                location_filter_applied=geo.location_filter_applied,
                results=[],
                retried=retried,
                resolved_zone=zone_meta.get('resolved_zone'),
                resolved_comarques=zone_meta.get('resolved_comarques'),
            )
            custom_meta['hint'] = 'radius_origin_unresolved'
            custom_meta['distance_km'] = radius_km
    else:
        location_filter, location_params = _territorial_location_predicate(geo)

    type_pattern: str | None = None
    if type:
        normalized = type.strip().lower()
        if normalized:
            type_pattern = f'%{normalized}%'

    query_text = (query or '').strip() or None
    query_pattern = _optional_pattern(query_text)

    params = (
        lang,
        *location_params,
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
            cursor.execute(
                _SEARCH_SQL.format(location_filter=location_filter),
                params,
            )
            rows = cursor.fetchall()
    finally:
        conn.close()

    cards = rows_to_cards(rows, 'establishment')

    if radius_km is not None and resolved_origin is not None:
        custom_meta = _build_radius_meta(
            origin=resolved_origin,
            distance_km=radius_km,
            results=cards,
        )

    wrapper_kwargs: dict[str, Any] = {
        'destination': destination,
        'results': cards,
        'total': str(len(cards)),
        'retried': retried,
        'type': type,
        'query': query_text,
        'lang': lang,
    }

    if custom_meta is not None:
        wrapper_kwargs['meta'] = custom_meta
        wrapper_kwargs['location_filter_applied'] = custom_meta.get(
            'location_filter_applied',
            True,
        )
    else:
        wrapper_kwargs['location_filter_applied'] = geo.location_filter_applied
        wrapper_kwargs.update(geo.meta_extras())

    return build_search_wrapper(**wrapper_kwargs)
