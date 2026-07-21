"""Geographic radius helpers for catalog searches (km from origin)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from app.db.connection import get_mysql_connection
from app.db.territory import is_broad_territory, normalize_territory

_EARTH_RADIUS_KM = 6371.0
_MIN_LAT = -90.0
_MAX_LAT = 90.0
_MIN_LNG = -180.0
_MAX_LNG = 180.0


@dataclass(frozen=True)
class OriginPoint:
    lat: float
    lng: float
    label: str
    source: str


def _destination_slug(destination: str) -> str:
    normalized = normalize_territory(destination)
    slug = re.sub(r'[^a-z0-9]+', '-', normalized)
    return slug.strip('-')


def _parse_float_coordinate(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(',', '.')
    if not text or text in {'0', '0.0'}:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_lat(value: object) -> float | None:
    parsed = _parse_float_coordinate(value)
    if parsed is None or not (_MIN_LAT <= parsed <= _MAX_LAT):
        return None
    return parsed


def _parse_lng(value: object) -> float | None:
    parsed = _parse_float_coordinate(value)
    if parsed is None or not (_MIN_LNG <= parsed <= _MAX_LNG):
        return None
    return parsed


def _parse_origin_row(
    row: dict | None,
    *,
    destination: str,
    source: str,
    lat_key: str = 'latitud',
    lng_key: str = 'longitud',
) -> OriginPoint | None:
    if not row:
        return None
    lat = _parse_lat(row.get(lat_key))
    lng = _parse_lng(row.get(lng_key))
    if lat is None or lng is None:
        return None
    label = str(row.get('poble') or row.get('ubicacio') or destination).strip() or destination
    return OriginPoint(lat=lat, lng=lng, label=label, source=source)


def _lookup_poble_origin(
    destination: str,
    *,
    config: Mapping[str, Any] | None = None,
) -> OriginPoint | None:
    slug = _destination_slug(destination)
    pattern = f'%{destination.strip()}%'
    sql = """
        SELECT latitud, longitud, poble
        FROM poble_general
        WHERE (%s <> '' AND param_url = %s)
           OR poble LIKE %s
        ORDER BY
            CASE WHEN %s <> '' AND param_url = %s THEN 0 ELSE 1 END,
            CHAR_LENGTH(poble)
        LIMIT 1
    """
    params = (slug, slug, pattern, slug, slug)
    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
    finally:
        conn.close()
    return _parse_origin_row(row, destination=destination, source='poble_general')


def _lookup_generic_origin(
    destination: str,
    *,
    config: Mapping[str, Any] | None = None,
) -> OriginPoint | None:
    slug = _destination_slug(destination)
    pattern = f'%{destination.strip()}%'
    sql = """
        SELECT latitud, longitud, ubicacio
        FROM generic_ubicacions
        WHERE (%s <> '' AND param_url = %s)
           OR ubicacio LIKE %s
        ORDER BY
            CASE WHEN %s <> '' AND param_url = %s THEN 0 ELSE 1 END,
            CHAR_LENGTH(ubicacio)
        LIMIT 1
    """
    params = (slug, slug, pattern, slug, slug)
    conn = get_mysql_connection(config)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
    finally:
        conn.close()
    return _parse_origin_row(row, destination=destination, source='generic_ubicacions')


def resolve_origin_coordinates(
    destination: str,
    *,
    config: Mapping[str, Any] | None = None,
) -> OriginPoint | None:
    """Resolve origin lat/lng for a destination name or slug."""
    text = (destination or '').strip()
    if not text or is_broad_territory(text):
        return None

    origin = _lookup_poble_origin(text, config=config)
    if origin is not None:
        return origin
    return _lookup_generic_origin(text, config=config)


def haversine_km_predicate(
    *,
    lat_expr: str,
    lng_expr: str,
    origin_lat: float,
    origin_lng: float,
    max_km: float,
) -> tuple[str, list[Any]]:
    """
    Build a parameterized Haversine distance predicate (km).

    Returns (sql_clause, params) suitable for: AND ({clause})
    """
    if max_km <= 0:
        return '(%s IS NULL)', [None]

    clause = f"""(
        {lat_expr} IS NOT NULL
        AND {lng_expr} IS NOT NULL
        AND {lat_expr} <> ''
        AND {lng_expr} <> ''
        AND (
            {_EARTH_RADIUS_KM} * ACOS(
                LEAST(
                    1.0,
                    GREATEST(
                        -1.0,
                        COS(RADIANS(%s)) * COS(RADIANS(CAST({lat_expr} AS DECIMAL(10, 6))))
                        * COS(RADIANS(CAST({lng_expr} AS DECIMAL(10, 6))) - RADIANS(%s))
                        + SIN(RADIANS(%s)) * SIN(RADIANS(CAST({lat_expr} AS DECIMAL(10, 6))))
                    )
                )
            )
        ) <= %s
    )"""
    params = [origin_lat, origin_lng, origin_lat, max_km]
    return clause, params


def build_radius_filter(
    origin: OriginPoint,
    *,
    lat_expr: str,
    lng_expr: str,
    max_km: float,
) -> tuple[str, list[Any]]:
    """Combine origin point with Haversine predicate."""
    return haversine_km_predicate(
        lat_expr=lat_expr,
        lng_expr=lng_expr,
        origin_lat=origin.lat,
        origin_lng=origin.lng,
        max_km=max_km,
    )
