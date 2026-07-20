"""Map database rows to normalized catalog card JSON."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Callable

CATALOG_BASE_URL = 'https://www.femturisme.cat'
DESCRIPTION_MAX_LEN = 200
SUPPORTED_CONTENT_TYPES = frozenset({
    'establishment', 'event', 'destination', 'article', 'route', 'experience',
})

_CARD_FIELDS = (
    'id',
    'type',
    'title',
    'location',
    'description',
    'url',
    'image',
    'date',
    'entity_id',
    'source_type',
    'source_id',
)


def row_to_card(row: dict, content_type: str) -> dict:
    """
    Map a DB row to a catalog card (tecnic §6.13).

    Target fields: id, type, title, location, description, url, image, date,
    entity_id, source_type, source_id (see docs/devs/preparacio-rag-cataleg.md).

    Args:
        row: Raw row dict from a repository query.
        content_type: Domain discriminator (establishment, event, destination, article, route, experience).

    Returns:
        Normalized card dict for results[].

    Raises:
        ValueError: Unsupported content_type.
    """
    if content_type not in SUPPORTED_CONTENT_TYPES:
        supported = ', '.join(sorted(SUPPORTED_CONTENT_TYPES))
        raise ValueError(
            f'Unsupported content_type={content_type!r}; expected one of: {supported}'
        )
    return _ROW_MAPPERS[content_type](row)


def rows_to_cards(rows: list[dict], content_type: str) -> list[dict]:
    """Map repository rows to cards, skipping rows without a title."""
    cards: list[dict] = []
    for row in rows:
        title = _clean_text(row.get('title'))
        if not title:
            continue
        cards.append(row_to_card(row, content_type))
    return cards


def build_search_meta(
    *,
    location_filter_applied: bool,
    results: list[dict],
    total: int | str | None = None,
    retried: bool = False,
    resolved_zone: str | None = None,
    resolved_comarques: list[str] | None = None,
) -> dict[str, Any]:
    """Build meta block so the LLM can interpret scope and empty results."""
    scope = 'location' if location_filter_applied else 'territory_wide'
    resolved_total = int(total) if total is not None else len(results)
    hint: str | None = None
    if len(results) == 0:
        hint = (
            'zero_results_with_location'
            if location_filter_applied
            else 'zero_results_territory_wide'
        )
    meta: dict[str, Any] = {
        'scope': scope,
        'location_filter_applied': location_filter_applied,
        'hint': hint,
        'truncated': resolved_total > len(results),
    }
    if retried:
        meta['retried'] = True
    if resolved_zone:
        meta['resolved_zone'] = resolved_zone
    if resolved_comarques:
        meta['resolved_comarques'] = resolved_comarques
    return meta


def build_search_wrapper(
    *,
    destination: str = '',
    results: list[dict],
    total: int | str | None = None,
    error: str | None = None,
    location_filter_applied: bool | None = None,
    retried: bool = False,
    **extra: object,
) -> dict:
    """
    Build the common catalog search wrapper JSON (tecnic §6.13).

    Extra keyword arguments (e.g. date_from, date_to, region) are merged into
    the wrapper for tool-specific fields. When location_filter_applied is set
    and meta is not provided, meta is built automatically.
    """
    if error:
        payload: dict[str, Any] = {
            'destination': destination,
            'total': '0',
            'results': [],
            'error': error,
        }
        payload.update(extra)
        return payload

    resolved_total = str(total) if total is not None else str(len(results))
    payload: dict[str, Any] = {
        'destination': destination,
        'total': resolved_total,
        'results': results,
        'error': None,
    }
    wrapper_extra = dict(extra)
    if location_filter_applied is not None and 'meta' not in wrapper_extra:
        zone_meta = geo_meta_from_extra(wrapper_extra)
        payload['meta'] = build_search_meta(
            location_filter_applied=location_filter_applied,
            results=results,
            total=resolved_total,
            retried=retried,
            **zone_meta,
        )
    payload.update(wrapper_extra)
    return payload


def geo_meta_from_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """Extract resolved_zone fields from wrapper extras into meta only."""
    zone_meta: dict[str, Any] = {}
    if 'resolved_zone' in extra:
        zone_meta['resolved_zone'] = extra.pop('resolved_zone')
    if 'resolved_comarques' in extra:
        zone_meta['resolved_comarques'] = extra.pop('resolved_comarques')
    return zone_meta


def _base_card() -> dict:
    return {field: None for field in _CARD_FIELDS}


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _truncate_description(value: object) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= DESCRIPTION_MAX_LEN:
        return text
    return text[: DESCRIPTION_MAX_LEN - 1].rstrip() + '…'


def _absolute_media_url(path: object) -> str | None:
    text = _clean_text(path)
    if not text:
        return None
    if text.startswith(('http://', 'https://')):
        return text
    return f'{CATALOG_BASE_URL.rstrip("/")}/{text.lstrip("/")}'


def _string_id(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _combine_location(location: object, region: object) -> str | None:
    loc = _clean_text(location)
    reg = _clean_text(region)
    if loc and reg and loc.lower() != reg.lower():
        return f'{loc} ({reg})'
    return loc or reg


def _combine_experience_location(
    establishment: object, location: object, comarca: object
) -> str | None:
    place = _combine_location(location, comarca)
    name = _clean_text(establishment)
    if name and place:
        return f'{name} ({place})'
    return name or place


def _build_establishment_url(type_code: object, param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    # Q-05 confirmat: fitxes individuals sempre a /establiments/{param_url}
    # (type_code és intern; no coincideix amb /on-dormir, /on-menjar ni /restaurants)
    return f'{CATALOG_BASE_URL}/establiments/{slug.strip("/")}'


def _build_destination_url(param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    return f'{CATALOG_BASE_URL}/pobles/{slug.strip("/")}'


def _build_event_url(param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    return f'{CATALOG_BASE_URL}/agenda/{slug.strip("/")}'


def _build_article_url(param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    return f'{CATALOG_BASE_URL}/noticies/{slug.strip("/")}'


def _build_route_url(param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    return f'{CATALOG_BASE_URL}/rutes/{slug.strip("/")}'


def _build_experience_url(param_url: object) -> str | None:
    slug = _clean_text(param_url)
    if not slug:
        return None
    return f'{CATALOG_BASE_URL}/ofertes/{slug.strip("/")}'


def _coerce_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _clean_text(value)
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _format_date_value(value: date) -> str:
    return value.strftime('%d/%m/%Y')


def _format_date_range(start: object, end: object) -> str | None:
    start_date = _coerce_date(start)
    end_date = _coerce_date(end)
    if start_date and end_date:
        if start_date == end_date:
            return _format_date_value(start_date)
        return f'{_format_date_value(start_date)} – {_format_date_value(end_date)}'
    if start_date:
        return _format_date_value(start_date)
    if end_date:
        return _format_date_value(end_date)
    return None


def _map_establishment(row: dict) -> dict:
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': _clean_text(row.get('type_label') or row.get('type')),
            'title': _clean_text(row.get('title')),
            'location': _combine_location(row.get('location'), row.get('comarca')),
            'description': _truncate_description(row.get('description')),
            'url': _build_establishment_url(row.get('type_code'), row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': None,
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'establishment',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


def _map_destination(row: dict) -> dict:
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': None,
            'title': _clean_text(row.get('title')),
            'location': _clean_text(row.get('region') or row.get('comarca')),
            'description': _truncate_description(row.get('description')),
            'url': _build_destination_url(row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': None,
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'destination',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


def _map_event(row: dict) -> dict:
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': None,
            'title': _clean_text(row.get('title')),
            'location': _combine_location(row.get('location'), row.get('comarca')),
            'description': _truncate_description(row.get('description')),
            'url': _build_event_url(row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': _format_date_range(row.get('date_start'), row.get('date_end')),
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'event',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


def _map_article(row: dict) -> dict:
    published = _coerce_date(row.get('published_at'))
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': None,
            'title': _clean_text(row.get('title')),
            'location': _clean_text(row.get('location')),
            'description': _truncate_description(row.get('description')),
            'url': _build_article_url(row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': _format_date_value(published) if published else None,
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'article',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


def _map_route(row: dict) -> dict:
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': _clean_text(row.get('route_type') or row.get('type')),
            'title': _clean_text(row.get('title')),
            'location': _combine_location(row.get('location'), row.get('comarca')),
            'description': _truncate_description(
                row.get('description') or row.get('introduccio')
            ),
            'url': _build_route_url(row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': None,
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'route',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


def _map_experience(row: dict) -> dict:
    card = _base_card()
    card.update(
        {
            'id': _string_id(row.get('id')),
            'type': _clean_text(row.get('category') or row.get('type')),
            'title': _clean_text(row.get('title')),
            'location': _combine_experience_location(
                row.get('establishment_name'),
                row.get('location'),
                row.get('comarca'),
            ),
            'description': _truncate_description(
                row.get('description') or row.get('resum')
            ),
            'url': _build_experience_url(row.get('param_url')),
            'image': _absolute_media_url(row.get('image')),
            'date': None,
            'entity_id': _clean_text(row.get('entity_id')),
            'source_type': 'experience',
            'source_id': _string_id(row.get('id')),
        }
    )
    return card


_ROW_MAPPERS: dict[str, Callable[[dict], dict]] = {
    'establishment': _map_establishment,
    'event': _map_event,
    'destination': _map_destination,
    'article': _map_article,
    'route': _map_route,
    'experience': _map_experience,
}


def entity_row_to_json(row: dict) -> dict:
    """Map a PostgreSQL entities row to admin API JSON (tecnic §9.4)."""
    entity_id = row.get('entity_id')
    created_at = row.get('created_at')
    updated_at = row.get('updated_at')
    config = row.get('config')
    if config is None:
        config = {}
    return {
        'entity_id': str(entity_id) if entity_id is not None else None,
        'name': row.get('name'),
        'entity_type': row.get('entity_type'),
        'slug': row.get('slug'),
        'territory': row.get('territory'),
        'config': config,
        'is_active': bool(row.get('is_active', True)),
        'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at,
        'updated_at': updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
    }


def document_row_to_json(row: dict) -> dict:
    """Map a PostgreSQL guide_documents row to admin API JSON (tecnic §9.5)."""
    doc_id = row.get('doc_id')
    entity_id = row.get('entity_id')
    indexed_at = row.get('indexed_at')
    created_at = row.get('created_at')
    updated_at = row.get('updated_at')
    return {
        'doc_id': str(doc_id) if doc_id is not None else None,
        'entity_id': str(entity_id) if entity_id is not None else None,
        'title': row.get('title'),
        'category': row.get('category'),
        'source_filename': row.get('source_filename'),
        'storage_path': row.get('storage_path'),
        'mime_type': row.get('mime_type'),
        'status': row.get('status'),
        'error_message': row.get('error_message'),
        'pages_count': int(row.get('pages_count') or 0),
        'chunks_count': int(row.get('chunks_count') or 0),
        'embedded_chunks_count': int(row.get('embedded_chunks_count') or 0),
        'embedding_model': row.get('embedding_model'),
        'version': int(row.get('version') or 1),
        'indexed_at': indexed_at.isoformat() if isinstance(indexed_at, datetime) else indexed_at,
        'created_at': created_at.isoformat() if isinstance(created_at, datetime) else created_at,
        'updated_at': updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
    }
