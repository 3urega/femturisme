"""Detect user message language for RF-10 (ca / es / en / fr)."""
from __future__ import annotations

import re
from typing import Literal

UserLanguage = Literal['ca', 'es', 'en', 'fr']

SUPPORTED_LANGS = frozenset({'ca', 'es', 'en', 'fr'})

_LANG_LABELS: dict[UserLanguage, str] = {
    'ca': 'català',
    'es': 'castellà',
    'en': 'anglès',
    'fr': 'francès',
}

_CA_MARKERS = (
    r'\bqu[èe]\b',
    r'\bquins?\b',
    r'\baquest',
    r'\bvols\b',
    r'\brecomaneu\b',
    r'\brecomana\b',
    r'\ballotjar',
    r'\bfires\b',
    r'\besdeveniments\b',
    r'\bcomarca\b',
    r'\bvisit(ar|eu)\b',
    r'\bsenderisme\b',
    r'\bfamília\b',
    r'\bfàcil\b',
    r"\bl'",
    r'\bmes\b',
    r'\bmés\b',
    r'\bper què\b',
    r'\bon\b',
    r'\bquin\b',
)

_ES_MARKERS = (
    r'\bqué\b',
    r'\bqué\b',
    r'\bcuál',
    r'\bcuáles',
    r'\brecomiénd',
    r'\bsenderismo\b',
    r'\bfácil\b',
    r'\bfamilia\b',
    r'\btambién\b',
    r'\bdónde\b',
    r'\bcómo\b',
    r'\btienes\b',
    r'\bquieres\b',
    r'\bpuedes\b',
    r'\bdime\b',
    r'\bhay\b',
    r'\brutas\b',
    r'¿',
    r'¡',
)

_EN_MARKERS = (
    r'\bwhat\b',
    r'\bwhere\b',
    r'\bwhich\b',
    r'\bwhen\b',
    r'\bhow\b',
    r'\bcan you\b',
    r'\brecommend\b',
    r'\broutes?\b',
    r'\bevents?\b',
    r'\bhotels?\b',
    r'\brestaurants?\b',
    r'\bthere\b',
    r'\bare there\b',
)

_FR_MARKERS = (
    r'\bquelles?\b',
    r'\bquels?\b',
    r'\boù\b',
    r'\bcomment\b',
    r'\bpouvez\b',
    r'\brandonnées?\b',
    r'\bévénements?\b',
    r'\bhôtels?\b',
    r'\brestaurants?\b',
    r'\bcatalogne\b',
    r'\bfrançais\b',
    r'\by a-t-il\b',
    r'\bje\b',
    r'\bdes\b',
)


def _count_marker_hits(text: str, patterns: tuple[str, ...]) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text))


def detect_user_language(message: str) -> UserLanguage:
    """
    Heuristic language detection for a single user turn.

    Defaults to Catalan when ambiguous (primary portal language).
    """
    text = (message or '').strip().lower()
    if not text:
        return 'ca'

    scores = {
        'ca': _count_marker_hits(text, _CA_MARKERS),
        'es': _count_marker_hits(text, _ES_MARKERS),
        'en': _count_marker_hits(text, _EN_MARKERS),
        'fr': _count_marker_hits(text, _FR_MARKERS),
    }

    if 'ç' in text or 'l·l' in text:
        scores['ca'] += 2
    if re.search(r'[àèòíú]', text) and scores['es'] == 0 and scores['fr'] == 0:
        scores['ca'] += 1
    if 'ñ' in text or '¿' in text or '¡' in text:
        scores['es'] += 2
    if re.search(r'\b(catalonia|emporda|barcelona)\b', text) and scores['en'] > 0:
        scores['en'] += 1
    if re.search(r'[êëïûù]', text) or re.search(r'\b(catalogne|randonnée)\b', text):
        scores['fr'] += 2

    best_lang = max(scores, key=scores.get)
    if scores[best_lang] == 0:
        return 'ca'
    return best_lang  # type: ignore[return-value]


def language_label(lang: str) -> str:
    """Human-readable label for prompts."""
    if lang in _LANG_LABELS:
        return _LANG_LABELS[lang]  # type: ignore[index]
    return 'català'


def foreign_language_markers(lang: UserLanguage) -> tuple[str, ...]:
    """Marker regexes from other languages (for lightweight UAT checks)."""
    mapping: dict[UserLanguage, tuple[str, ...]] = {
        'ca': _ES_MARKERS + _EN_MARKERS + _FR_MARKERS,
        'es': _CA_MARKERS + _EN_MARKERS + _FR_MARKERS,
        'en': _CA_MARKERS + _ES_MARKERS + _FR_MARKERS,
        'fr': _CA_MARKERS + _ES_MARKERS + _EN_MARKERS,
    }
    return mapping.get(lang, ())
