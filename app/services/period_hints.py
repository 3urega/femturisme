"""Infer calendar periods from natural-language user messages."""
from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_MONTH_ALIASES: dict[str, int] = {
    'gener': 1,
    'january': 1,
    'jan': 1,
    'febrer': 2,
    'february': 2,
    'feb': 2,
    'març': 3,
    'marzo': 3,
    'march': 3,
    'mar': 3,
    'abril': 4,
    'april': 4,
    'abr': 4,
    'maig': 5,
    'mayo': 5,
    'may': 5,
    'juny': 6,
    'junio': 6,
    'june': 6,
    'jun': 6,
    'juliol': 7,
    'julio': 7,
    'july': 7,
    'jul': 7,
    'agost': 8,
    'august': 8,
    'ago': 8,
    'setembre': 9,
    'septiembre': 9,
    'september': 9,
    'sep': 9,
    'set': 9,
    'octubre': 10,
    'october': 10,
    'oct': 10,
    'novembre': 11,
    'noviembre': 11,
    'november': 11,
    'nov': 11,
    'desembre': 12,
    'diciembre': 12,
    'december': 12,
    'dec': 12,
    'dic': 12,
}

_THIS_MONTH_PATTERNS = (
    r'\baquest\s+mes\b',
    r'\bper\s+aquest\s+mes\b',
    r'\beste\s+mes\b',
    r'\bthis\s+month\b',
    r'\bel\s+mes\b',
    r'\bdurant\s+aquest\s+mes\b',
    r'\bara\s+mateix\b',
    r'\bactualment\b',
)

_AGENDA_SEARCH_PATTERNS = (
    r'\bevents?\b',
    r'\bfira\b',
    r'\bfires\b',
    r'\bfestes?\b',
    r'\bagenda\b',
    r'\bfestivals?\b',
    r'\bactivitats?\b',
)

_AGENDA_META_PATTERNS = (
    r'\bqu[eè]\s+(és|es|son|són)\b',
    r'\bwhat\s+(is|are)\b',
    r'\bdiferència\b',
    r'\bdiferencia\b',
)

_RELATIVE_TIME_MARKERS = (
    r'\baquest\b',
    r'\baquesta\b',
    r'\beste\b',
    r'\besta\b',
    r'\bthis\b',
    r'\bavui\b',
    r'\bdemà\b',
    r'\bmañana\b',
)

_THIS_WEEKEND_PATTERNS = (
    r"\baquest\s+cap\s+de\s+setmana\b",
    r'\beste\s+fin\s+de\s+semana\b',
    r'\bthis\s+weekend\b',
    r'\bel\s+cap\s+de\s+setmana\b',
    r'\bfin\s+de\s+semana\b',
)

_TODAY_PATTERNS = (
    r'\bavui\b',
    r'\bhoy\b',
    r'\btoday\b',
)

_TOMORROW_PATTERNS = (
    r'\bdemà\b',
    r'\bdemà\b',
    r'\bmañana\b',
    r'\btomorrow\b',
)

_THIS_WEEK_PATTERNS = (
    r'\baquesta\s+setmana\b',
    r'\besta\s+semana\b',
    r'\bthis\s+week\b',
)


def _normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _this_weekend_bounds(today: date) -> tuple[date, date]:
    weekday = today.weekday()  # Mon=0 … Sun=6
    if weekday == 5:
        return today, today + timedelta(days=1)
    if weekday == 6:
        return today, today
    days_until_saturday = (5 - weekday) % 7
    saturday = today + timedelta(days=days_until_saturday)
    return saturday, saturday + timedelta(days=1)


def _this_week_bounds(today: date) -> tuple[date, date]:
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _match_month_name(text: str, today: date) -> tuple[date, date] | None:
    for name, month in _MONTH_ALIASES.items():
        if re.search(rf'\b{re.escape(name)}\b', text):
            return _month_bounds(today.year, month)
    return None


def _has_relative_time_marker(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(re.search(pattern, normalized) for pattern in _RELATIVE_TIME_MARKERS)


def _parse_iso_date(value: object) -> date | None:
    if value is None:
        return None
    text = str(value).strip()[:10]
    if len(text) != 10:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _correct_stale_llm_dates(
    tool_input: dict,
    user_message: str,
    *,
    today: date,
) -> dict | None:
    """When the user asks relatively but the LLM sends an old year, fix to current month."""
    if not _has_relative_time_marker(user_message):
        return None
    parsed_from = _parse_iso_date(tool_input.get('date_from'))
    if parsed_from is None or parsed_from.year >= today.year:
        return None
    start, end = _month_bounds(today.year, today.month)
    merged = dict(tool_input)
    merged['date_from'] = start.isoformat()
    merged['date_to'] = end.isoformat()
    merged['_period_hint_applied'] = True
    merged['_stale_dates_corrected'] = True
    return merged


def _explicit_year_in_message(text: str) -> int | None:
    match = re.search(r'\b(20\d{2})\b', _normalize_text(text))
    return int(match.group(1)) if match else None


def _sanitize_hallucinated_year(
    tool_input: dict,
    user_message: str,
    *,
    today: date,
) -> dict | None:
    """
    Drop or fix LLM dates from a past year when the user did not ask for that year.

    Example failure mode: user says «aquest mes» (juliol 2026) but LLM sends 2024-06.
    """
    parsed_from = _parse_iso_date(tool_input.get('date_from'))
    if parsed_from is None:
        return None

    explicit_year = _explicit_year_in_message(user_message)
    if parsed_from.year >= today.year:
        return None
    if explicit_year == parsed_from.year:
        return None

    merged = dict(tool_input)
    if any(re.search(pattern, _normalize_text(user_message)) for pattern in _THIS_MONTH_PATTERNS):
        start, end = _month_bounds(today.year, today.month)
        merged['date_from'] = start.isoformat()
        merged['date_to'] = end.isoformat()
        merged['_period_hint_applied'] = True
        merged['_stale_dates_corrected'] = True
        return merged

    merged.pop('date_from', None)
    merged.pop('date_to', None)
    merged['_stale_dates_removed'] = True
    return merged


def infer_event_period(
    user_message: str,
    *,
    today: date | None = None,
) -> tuple[str, str] | None:
    """
    Return (date_from, date_to) as YYYY-MM-DD when the message implies a period.

    Priority: today/tomorrow > weekend > week > this month > explicit month name.
    """
    reference = today or date.today()
    text = _normalize_text(user_message)
    if not text:
        return None

    if any(re.search(pattern, text) for pattern in _TODAY_PATTERNS):
        iso = reference.isoformat()
        return iso, iso

    if any(re.search(pattern, text) for pattern in _TOMORROW_PATTERNS):
        tomorrow = reference + timedelta(days=1)
        iso = tomorrow.isoformat()
        return iso, iso

    if any(re.search(pattern, text) for pattern in _THIS_WEEKEND_PATTERNS):
        start, end = _this_weekend_bounds(reference)
        return start.isoformat(), end.isoformat()

    if any(re.search(pattern, text) for pattern in _THIS_WEEK_PATTERNS):
        start, end = _this_week_bounds(reference)
        return start.isoformat(), end.isoformat()

    if any(re.search(pattern, text) for pattern in _THIS_MONTH_PATTERNS):
        start, end = _month_bounds(reference.year, reference.month)
        return start.isoformat(), end.isoformat()

    month_bounds = _match_month_name(text, reference)
    if month_bounds:
        return month_bounds[0].isoformat(), month_bounds[1].isoformat()

    return None


def apply_event_period_hints(
    tool_name: str,
    tool_input: dict,
    user_message: str,
    *,
    today: date | None = None,
) -> dict:
    """
    Override search_events date_from/date_to when the user message implies a period.

    The server-side hint wins over incorrect LLM dates (e.g. past years).
    """
    if tool_name != 'search_events':
        return tool_input

    period = infer_event_period(user_message, today=today)
    if period is not None:
        date_from, date_to = period
        merged = dict(tool_input)
        merged['date_from'] = date_from
        merged['date_to'] = date_to
        merged['_period_hint_applied'] = True
        return merged

    reference = today or date.today()
    corrected = _correct_stale_llm_dates(tool_input, user_message, today=reference)
    if corrected is not None:
        return corrected

    sanitized = _sanitize_hallucinated_year(tool_input, user_message, today=reference)
    if sanitized is not None:
        return sanitized

    return tool_input


def is_agenda_search_query(user_message: str) -> bool:
    """True when the user wants a catalog agenda lookup (not a meta/explanation question)."""
    text = _normalize_text(user_message)
    if not text:
        return False
    if any(re.search(pattern, text) for pattern in _AGENDA_META_PATTERNS):
        return False
    if not any(re.search(pattern, text) for pattern in _AGENDA_SEARCH_PATTERNS):
        return False
    if infer_event_period(user_message) is not None:
        return True
    if re.search(r'\b(catalunya|andorra|bergued|empord|barcelona|girona|garrotxa|pirineu)\b', text):
        return True
    if re.search(r"\b(?:a|al|a l')\s+[\wàèéíòóúç\-']", text):
        return True
    return False


def infer_agenda_destination(user_message: str) -> str | None:
    text = _normalize_text(user_message)
    if re.search(r'\bcatalunya\b', text) or re.search(r'\btot catalunya\b', text):
        return 'Catalunya'
    if re.search(r'\bandorra\b', text):
        return 'Andorra'
    match = re.search(
        r"\b(?:a|al|a l'|en)\s+([a-zàèéíòóúç][a-zàèéíòóúç\s\-']{2,})",
        text,
    )
    if match:
        destination = match.group(1).strip(' ?.,')
        stop_words = {'aquest', 'aquesta', 'este', 'esta', 'this', 'mes', 'cap', 'setmana'}
        if destination and destination.split()[0] not in stop_words:
            return destination[:1].upper() + destination[1:]
    return None


def build_forced_search_events_input(
    user_message: str,
    *,
    today: date | None = None,
) -> dict | None:
    """Build a search_events payload when the LLM must be overridden."""
    if not is_agenda_search_query(user_message):
        return None
    destination = infer_agenda_destination(user_message)
    if not destination and infer_event_period(user_message, today=today):
        destination = 'Catalunya'
    if not destination:
        return None
    return apply_event_period_hints(
        'search_events',
        {'destination': destination},
        user_message,
        today=today,
    )
