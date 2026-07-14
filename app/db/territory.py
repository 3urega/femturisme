"""Territory helpers for catalog geo filters."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal, Mapping

from app.db.connection import get_mysql_connection

_BROAD_TERRITORY_ALIASES = frozenset({
    'andorra',
    'catalonia',
    'cataluna',
    'cataluña',
    'catalunya',
    'ccaa',
    'comunitat autonoma de catalunya',
    'comunitat autònoma de catalunya',
    'tot catalunya',
    'toda cataluña',
    'toda catalunya',
    'tothom catalunya',
})

# Tourism zones → comarca param_url slugs in generic_ubicacions (CMS).
_PIRINEU_COMARQUES = (
    'alt-urgell',
    'bergueda',
    'cerdanya',
    'garrotxa',
    'la-noguera',
    'pallars-jussa',
    'pallars-sobira',
    'pla-urgell',
    'ripolles',
    'solsones',
    'urgell',
    'val-aran',
)

_TOURISM_ZONE_COMPOSITION: dict[str, tuple[str, ...]] = {
    'costa brava': ('alt-emporda', 'baix-emporda', 'la-selva'),
    'la costa brava': ('alt-emporda', 'baix-emporda', 'la-selva'),
    'pirineu': _PIRINEU_COMARQUES,
    'el pirineu': _PIRINEU_COMARQUES,
}

_COMARCA_DISPLAY_NAMES: dict[str, str] = {
    'alt-emporda': 'Alt Empordà',
    'baix-emporda': 'Baix Empordà',
    'la-selva': 'La Selva',
    'alt-urgell': 'Alt Urgell',
    'bergueda': 'Berguedà',
    'cerdanya': 'Cerdanya',
    'garrotxa': 'Garrotxa',
    'la-noguera': 'La Noguera',
    'pallars-jussa': 'Pallars Jussà',
    'pallars-sobira': 'Pallars Sobirà',
    'pla-urgell': "Pla d'Urgell",
    'ripolles': 'Ripollès',
    'solsones': 'Solsonès',
    'urgell': 'Urgell',
    'val-aran': "Val d'Aran",
}


@dataclass(frozen=True)
class GeoFilter:
    """Resolved geographic filter for catalog SQL queries."""

    kind: Literal['none', 'like', 'poble_ids']
    pattern: str | None = None
    poble_ids: tuple[int, ...] = ()
    resolved_zone: str | None = None
    resolved_comarques: tuple[str, ...] = ()
    location_filter_applied: bool = False

    def meta_extras(self) -> dict[str, Any]:
        if not self.resolved_zone:
            return {}
        extras: dict[str, Any] = {'resolved_zone': self.resolved_zone}
        if self.resolved_comarques:
            extras['resolved_comarques'] = list(self.resolved_comarques)
        return extras


def normalize_territory(text: str) -> str:
    """Lowercase, strip accents and collapse whitespace."""
    value = (text or '').strip().lower()
    if not value:
        return ''
    normalized = unicodedata.normalize('NFKD', value)
    without_accents = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    collapsed = re.sub(r'\s+', ' ', without_accents)
    return collapsed.strip()


def is_broad_territory(text: str) -> bool:
    """True when destination means whole Catalonia/Andorra, not a town/comarca."""
    normalized = normalize_territory(text)
    if not normalized:
        return False
    if normalized in _BROAD_TERRITORY_ALIASES:
        return True
    return normalized.startswith('tot catalun') or normalized.startswith('toda catalun')


def _parse_poble_ids(raw: str | None) -> tuple[int, ...]:
    if not raw:
        return ()
    ids: list[int] = []
    for token in raw.replace("'", '').split(','):
        token = token.strip()
        if token.isdigit():
            ids.append(int(token))
    return tuple(ids)


@lru_cache(maxsize=16)
def _load_poble_ids_for_comarques(comarca_keys: tuple[str, ...]) -> tuple[int, ...]:
    if not comarca_keys:
        return ()
    placeholders = ','.join(['%s'] * len(comarca_keys))
    sql = (
        f'SELECT id_pobles FROM generic_ubicacions '
        f'WHERE param_url IN ({placeholders})'
    )
    conn = get_mysql_connection()
    merged: set[int] = set()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, comarca_keys)
            for row in cursor.fetchall():
                merged.update(_parse_poble_ids(row.get('id_pobles')))
    finally:
        conn.close()
    return tuple(sorted(merged))


def _resolve_tourism_zone(normalized: str, original: str) -> GeoFilter | None:
    composition = _TOURISM_ZONE_COMPOSITION.get(normalized)
    if not composition:
        return None
    poble_ids = _load_poble_ids_for_comarques(composition)
    comarques = tuple(
        _COMARCA_DISPLAY_NAMES.get(key, key) for key in composition
    )
    display_zone = original.strip() or normalized.title()
    return GeoFilter(
        kind='poble_ids',
        poble_ids=poble_ids,
        resolved_zone=display_zone,
        resolved_comarques=comarques,
        location_filter_applied=True,
    )


def resolve_geo_filter(
    destination: str,
    *,
    skip_location_filter: bool = False,
    config: Mapping[str, Any] | None = None,
) -> GeoFilter:
    """
    Resolve destination to a typed geo filter (broad / LIKE / poble ID list).

    Tourism zones (e.g. Costa Brava) expand to municipality IDs from
    generic_ubicacions comarca rows in the CMS.
    """
    del config  # reserved for tests; cache uses default connection
    if skip_location_filter or is_broad_territory(destination):
        return GeoFilter(kind='none', location_filter_applied=False)

    text = destination.strip()
    if not text:
        return GeoFilter(kind='none', location_filter_applied=False)

    normalized = normalize_territory(text)
    zone_filter = _resolve_tourism_zone(normalized, text)
    if zone_filter is not None:
        return zone_filter

    return GeoFilter(
        kind='like',
        pattern=f'%{text}%',
        location_filter_applied=True,
    )


def location_predicate(
    geo: GeoFilter,
    *,
    poble_id_col: str = 'pg.id',
    poble_like_col: str = 'pg.poble',
    comarca_like_col: str = 'pc.comarca',
    param_url_like_col: str | None = None,
    extra_poble_id_cols: tuple[str, ...] = (),
    extra_like_pairs: tuple[tuple[str, str], ...] = (),
) -> tuple[str, list[Any]]:
    """
    Build a SQL boolean fragment and bind params for a location filter.

    Returns (clause, params) to embed as: AND {clause}
    """
    if geo.kind == 'none':
        return '(%s IS NULL)', [None]

    if geo.kind == 'poble_ids':
        if not geo.poble_ids:
            return '(%s IS NULL)', [None]
        id_cols = (poble_id_col, *extra_poble_id_cols)
        placeholders = ','.join(['%s'] * len(geo.poble_ids))
        in_clauses = [f'{col} IN ({placeholders})' for col in id_cols]
        params: list[Any] = [1]
        for _ in id_cols:
            params.extend(geo.poble_ids)
        joined = ' OR '.join(in_clauses)
        return f'(%s IS NOT NULL AND ({joined}))', params

    pattern = geo.pattern or ''
    like_parts = [
        f'{poble_like_col} LIKE %s',
        f'{comarca_like_col} LIKE %s',
    ]
    if param_url_like_col:
        like_parts.append(f'{param_url_like_col} LIKE %s')
    for poble_col, comarca_col in extra_like_pairs:
        like_parts.append(f'{poble_col} LIKE %s')
        like_parts.append(f'{comarca_col} LIKE %s')
    # First bind is the IS NULL guard; must be non-null when filtering (legacy contract).
    params = [pattern, *([pattern] * len(like_parts))]
    return f'(%s IS NULL OR {" OR ".join(like_parts)})', params


def resolve_location_filter(
    destination: str,
    *,
    skip_location_filter: bool = False,
) -> tuple[str | None, bool]:
    """
    Return (LIKE pattern or None, location_filter_applied).

    Legacy helper for LIKE-only filters. Prefer resolve_geo_filter() for
    tourism zones that resolve to poble ID lists.
    """
    geo = resolve_geo_filter(
        destination,
        skip_location_filter=skip_location_filter,
    )
    if geo.kind == 'none':
        return None, False
    if geo.kind == 'like':
        return geo.pattern, geo.location_filter_applied
    return None, geo.location_filter_applied
