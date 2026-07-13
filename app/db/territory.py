"""Territory helpers for catalog geo filters."""
from __future__ import annotations

import re
import unicodedata

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


def resolve_location_filter(
    destination: str,
    *,
    skip_location_filter: bool = False,
) -> tuple[str | None, bool]:
    """
    Return (LIKE pattern or None, location_filter_applied).

    Broad territory and explicit skip drop the poble/comarca filter.
    """
    if skip_location_filter or is_broad_territory(destination):
        return None, False
    text = destination.strip()
    if not text:
        return None, False
    return f'%{text}%', True
