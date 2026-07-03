"""
Shared scraping helpers for femturisme.cat

All pages are fully scrapable with plain requests — no bot protection.
Card structure: a.ft-card with data-el-id, data-el-type, .ft-card__title,
                .ft-card__loc, .ft-item-desc, href, data-wl-img
Location filter: ?ubicacio=<town_or_region>
"""
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.femturisme.cat'

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ca-ES,ca;q=0.9',
}


def fetch_page(path: str, params: dict | None = None) -> BeautifulSoup | None:
    url = BASE_URL + path
    try:
        r = requests.get(url, headers=_HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')
    except requests.RequestException:
        return None


def extract_cards(soup: BeautifulSoup, limit: int = 8) -> list[dict]:
    """Extract a.ft-card elements and normalise to a common dict."""
    cards = []
    for a in soup.select('a.ft-card'):
        wl_btn = a.select_one('[data-wl-img]')
        media  = a.select_one('.ft-card__media')

        image = None
        if wl_btn and wl_btn.get('data-wl-img'):
            image = wl_btn['data-wl-img']
        elif media:
            m = re.search(r"url\(['\"]?([^'\"()]+)['\"]?\)", media.get('style', ''))
            if m:
                image = m.group(1)

        card = {
            'id':          a.get('data-el-id'),
            'type':        a.get('data-el-type'),
            'title':       _text(a, '.ft-card__title,h2,h3,h4'),
            'location':    _text(a, '.ft-card__loc'),
            'description': _text(a, '.ft-item-desc,p'),
            'url':         a.get('href'),
            'image':       image,
        }
        if card['title']:
            cards.append(card)
        if len(cards) >= limit:
            break
    return cards


def result_count(soup: BeautifulSoup) -> str | None:
    el = soup.select_one('.ft-filter-bar__count')
    return el.get_text(strip=True) if el else None


def _text(el, sel: str) -> str | None:
    found = el.select_one(sel)
    return found.get_text(strip=True) if found else None
