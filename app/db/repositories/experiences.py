"""MySQL repository for promotional experiences (ofertes)."""
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
  AND {location_filter}
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


def search(
    *,
    destination: str,
    category: str | None = None,
    establishment: str | None = None,
    lang: str = 'ca',
    limit: int = 20,
    distance_km: float | int | None = None,
    skip_location_filter: bool = False,
    retried: bool = False,
    config: Mapping[str, Any] | None = None,
) -> dict:
    """
    Search promotional experiences and offers by destination and optional filters.

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
            location_filter, location_params = location_predicate(geo)
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
        location_filter, location_params = location_predicate(geo)

    category_text = (category or '').strip() or None
    establishment_text = (establishment or '').strip() or None
    category_pattern = _optional_pattern(category_text)
    establishment_pattern = _optional_pattern(establishment_text)

    params = (
        lang,
        *location_params,
        category_pattern,
        category_pattern,
        establishment_pattern,
        establishment_pattern,
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

    cards = rows_to_cards(rows, 'experience')

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
        'category': category_text,
        'establishment': establishment_text,
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
