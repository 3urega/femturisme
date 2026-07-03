"""
Phase 3: clean extraction of real data for each tool category
"""
import sys
sys.path.insert(0, '/projects/restaurants/venv/lib/python3.11/site-packages')

import requests
from bs4 import BeautifulSoup
import re, json, time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ca-ES,ca;q=0.9',
}

BASE = 'https://www.femturisme.cat'

def fetch(path):
    url = BASE + path
    r = requests.get(url, headers=HEADERS, timeout=15)
    print(f"  [{r.status_code}] {url}")
    return BeautifulSoup(r.text, 'html.parser') if r.status_code == 200 else None

def extract_cards(soup, limit=5):
    """Extract ft-card anchor elements (the real cards, not child divs)."""
    cards = []
    for a in soup.select('a.ft-card'):
        media = a.select_one('.ft-card__media')
        wl_btn = a.select_one('[data-wl-img]')

        # Image: prefer data-wl-img (clean URL), fallback to CSS background-image
        img = None
        if wl_btn and wl_btn.get('data-wl-img'):
            img = wl_btn['data-wl-img']
        elif media:
            m = re.search(r"url\(['\"]?([^'\"()]+)['\"]?\)", media.get('style', ''))
            if m:
                img = m.group(1)

        card = {
            'id':          a.get('data-el-id'),
            'type':        a.get('data-el-type'),
            'title':       _text(a, 'h2,h3,h4,.ft-card__title'),
            'location':    _text(a, '.ft-card__loc'),
            'description': _text(a, '.ft-item-desc,p'),
            'url':         a.get('href'),
            'image':       img,
        }
        cards.append(card)
        if len(cards) >= limit:
            break
    return cards

def extract_event_cards(soup, limit=5):
    """Event cards use ft-event-card class."""
    cards = []
    # Events seem to use ft-card too — try both
    for a in soup.select('a.ft-card, a.ft-event-card'):
        card = {
            'id':       a.get('data-el-id'),
            'type':     a.get('data-el-type', 'event'),
            'title':    _text(a, '.ft-card__title,.ft-event-card__title,h2,h3,h4'),
            'date':     _text(a, '.ft-card__loc,.ft-event-card__subtitle'),
            'location': _text(a, '.ft-card__place'),
            'url':      a.get('href'),
        }
        if card['title']:
            cards.append(card)
        if len(cards) >= limit:
            break
    return cards

def _text(el, sel):
    found = el.select_one(sel)
    return found.get_text(strip=True) if found else None

# ── Routes ────────────────────────────────────────────────────────────────────
print("=" * 60)
print("ROUTES  /rutes")
print("=" * 60)
soup = fetch('/rutes')
if soup:
    # Check filter chips (difficulty, type)
    chips = [c.get_text(strip=True) for c in soup.select('.ft-chip')]
    print(f"  Filter chips: {chips[:15]}")
    cards = extract_cards(soup, limit=5)
    print(f"  Cards extracted: {len(cards)}")
    for c in cards:
        print(json.dumps(c, ensure_ascii=False, indent=4))

time.sleep(1)

# ── Agenda / Events ───────────────────────────────────────────────────────────
print()
print("=" * 60)
print("AGENDA  /agenda")
print("=" * 60)
soup = fetch('/agenda')
if soup:
    chips = [c.get_text(strip=True) for c in soup.select('.ft-chip')]
    print(f"  Filter chips: {chips[:15]}")
    cards = extract_event_cards(soup, limit=5)
    print(f"  Cards extracted: {len(cards)}")
    for c in cards:
        print(json.dumps(c, ensure_ascii=False, indent=4))

time.sleep(1)

# ── Experiences / Offers ──────────────────────────────────────────────────────
print()
print("=" * 60)
print("OFERTES  /ofertes")
print("=" * 60)
soup = fetch('/ofertes')
if soup:
    chips = [c.get_text(strip=True) for c in soup.select('.ft-chip')]
    print(f"  Filter chips: {chips[:15]}")
    cards = extract_cards(soup, limit=5)
    print(f"  Cards extracted: {len(cards)}")
    for c in cards:
        print(json.dumps(c, ensure_ascii=False, indent=4))

time.sleep(1)

# ── Accommodations ─────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("ON DORMIR  /on-dormir")
print("=" * 60)
soup = fetch('/on-dormir')
if soup:
    chips = [c.get_text(strip=True) for c in soup.select('.ft-chip')]
    print(f"  Filter chips: {chips[:15]}")
    cards = extract_cards(soup, limit=5)
    print(f"  Cards extracted: {len(cards)}")
    for c in cards:
        print(json.dumps(c, ensure_ascii=False, indent=4))

time.sleep(1)

# ── Restaurants ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("ON MENJAR  /on-menjar")
print("=" * 60)
soup = fetch('/on-menjar')
if soup:
    chips = [c.get_text(strip=True) for c in soup.select('.ft-chip')]
    print(f"  Filter chips: {chips[:15]}")
    cards = extract_cards(soup, limit=5)
    print(f"  Cards extracted: {len(cards)}")
    for c in cards:
        print(json.dumps(c, ensure_ascii=False, indent=4))

time.sleep(1)

# ── URL filtering — test ?query= param ────────────────────────────────────────
print()
print("=" * 60)
print("FILTER TEST — rutes with location query")
print("=" * 60)
for qs in ['?ubicacio=berga', '?q=berga', '?comarca=bergueda', '?cerca=berga']:
    soup = fetch('/rutes' + qs)
    if soup:
        cards = extract_cards(soup, limit=2)
        count_el = soup.select_one('.ft-filter-bar__count')
        count = count_el.get_text(strip=True) if count_el else '?'
        print(f"  {qs}: {count}, {len(cards)} cards parsed")
        if cards:
            print(f"    First: {cards[0]['title']} — {cards[0]['location']}")
