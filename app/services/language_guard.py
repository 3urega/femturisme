"""Lightweight reply polish so Catalan answers avoid common Castilian slips."""
from __future__ import annotations

import re

from app.services.user_language import detect_user_language

_CA_USER_MARKERS = (
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
)

_ES_USER_MARKERS = (
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
)

_CA_CASTILIAN_FIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r'\bdime-ho\b', re.I), "digues-m'ho"),
    (re.compile(r'\bdimelo\b', re.I), "digues-m'ho"),
    (re.compile(r'\bdime\b', re.I), 'digues-me'),
    (re.compile(r'\btienes\b', re.I), 'tens'),
    (re.compile(r'\bquieres\b', re.I), 'vols'),
    (re.compile(r'\bpuedes\b', re.I), 'pots'),
    (re.compile(r'\baquí tienes\b', re.I), 'aquí tens'),
    (re.compile(r'\bháblame\b', re.I), "parla'm"),
)


def is_catalan_user_message(user_message: str) -> bool:
    text = (user_message or '').strip().lower()
    if not text:
        return False
    if any(re.search(pattern, text) for pattern in _ES_USER_MARKERS):
        return False
    if 'ç' in text or 'à' in text or 'l·l' in text:
        return True
    return any(re.search(pattern, text) for pattern in _CA_USER_MARKERS)


def polish_catalan_reply(text: str) -> str:
    """Replace frequent Castilian forms when the user asked in Catalan."""
    polished = text
    for pattern, replacement in _CA_CASTILIAN_FIXES:
        polished = pattern.sub(replacement, polished)
    return polished


def polish_reply_for_user(user_message: str, reply: str) -> str:
    if detect_user_language(user_message) != 'ca':
        return reply
    return polish_catalan_reply(reply)
