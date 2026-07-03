"""
Phase 2: find correct URLs and extract real card data from femturisme.cat
"""
import sys
sys.path.insert(0, '/projects/restaurants/venv/lib/python3.11/site-packages')

import requests
from bs4 import BeautifulSoup
import re, json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ca-ES,ca;q=0.9',
}

def get(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    print(f"  [{r.status_code}] {url}")
    if r.status_code == 200:
        return BeautifulSoup(r.text, 'html.parser')
    return None

# ── 1. Discover correct URLs from the home nav ──────────────────────────────
print("=" * 60)
print("STEP 1 — Discover nav links from home")
print("=" * 60)
soup_home = get('https://www.femturisme.cat/')
if soup_home:
    nav_links = soup_home.select('nav a[href], header a[href]')
    seen = set()
    for a in nav_links:
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if href and href not in seen and 'femturisme' not in href:
            seen.add(href)
            print(f"  {text!r:30s} -> {href}")

# ── 2. Also look at all internal links on home page ─────────────────────────
print()
print("STEP 2 — All unique path patterns on home page")
print("=" * 60)
if soup_home:
    paths = set()
    for a in soup_home.find_all('a', href=True):
        href = a['href']
        if href.startswith('/') or 'femturisme.cat/' in href:
            # Extract path
            path = re.sub(r'https?://[^/]+', '', href).split('?')[0].strip('/')
            if path and len(path) < 60:
                parts = path.split('/')
                if len(parts) <= 3:
                    paths.add('/' + path)
    for p in sorted(paths):
        print(f"  {p}")

# ── 3. Fetch the correct section pages ──────────────────────────────────────
print()
print("STEP 3 — Fetch section pages and extract cards")
print("=" * 60)

candidate_urls = {
    'ofertes/experiences': 'https://www.femturisme.cat/ofertes',
    'que-fer':             'https://www.femturisme.cat/que-fer-aquest-cap-de-setmana',
    'agenda':              'https://www.femturisme.cat/agenda',
    'rutes':               'https://www.femturisme.cat/ca/rutes',
    'allotjaments':        'https://www.femturisme.cat/allotjaments',
    'establiments':        'https://www.femturisme.cat/establiments',
}

for label, url in candidate_urls.items():
    soup = get(url)
    if not soup:
        continue
    title = soup.title.string.strip() if soup.title else ''
    print(f"    Title: {title}")

    # Try ft-card selectors (the site uses ft- prefix)
    for sel in [
        '[class*="ft-card"]', '[class*="ft-item"]', '[class*="ft-result"]',
        'article', '.card',
        '[class*="card-"]',
    ]:
        items = soup.select(sel)
        if items:
            print(f"    Selector '{sel}': {len(items)} items")
            # Show first item structure
            first = items[0]
            img   = first.select_one('img')
            link  = first.select_one('a[href]')
            title_el = first.select_one('h2,h3,h4,.title,[class*="title"],[class*="name"]')
            desc_el  = first.select_one('p,[class*="desc"],[class*="text"]')
            cat_el   = first.select_one('[class*="cat"],[class*="tag"],[class*="type"],[class*="label"]')
            print(f"      img   : {img['src'][:80] if img else None}")
            print(f"      link  : {link['href'][:80] if link else None}")
            print(f"      title : {title_el.get_text(strip=True)[:60] if title_el else None}")
            print(f"      desc  : {desc_el.get_text(strip=True)[:80] if desc_el else None}")
            print(f"      cat   : {cat_el.get_text(strip=True)[:40] if cat_el else None}")
            break
    print()

# ── 4. Deep-dive into routes page ───────────────────────────────────────────
print("STEP 4 — Deep-dive routes page, extract 3 real items")
print("=" * 60)
soup_routes = get('https://www.femturisme.cat/ca/rutes')
if soup_routes:
    # Print all classes used on the page to find the right selectors
    all_classes = set()
    for el in soup_routes.find_all(class_=True):
        for c in el['class']:
            if c.startswith('ft-'):
                all_classes.add(c)
    print("  ft-* CSS classes found:", sorted(all_classes)[:40])

    # Try to grab route cards
    for sel in ['[class*="ft-card"]', 'article', '[class*="route"]', '[class*="ruta"]']:
        items = soup_routes.select(sel)
        if items:
            print(f"\n  Found {len(items)} items with '{sel}'")
            for item in items[:3]:
                print(f"  ---")
                print(f"  HTML snippet: {str(item)[:400]}")
            break

# ── 5. Agenda page ──────────────────────────────────────────────────────────
print()
print("STEP 5 — Agenda page ft-* classes and sample cards")
print("=" * 60)
soup_agenda = get('https://www.femturisme.cat/ca/agenda')
if soup_agenda:
    all_classes = set()
    for el in soup_agenda.find_all(class_=True):
        for c in el['class']:
            if c.startswith('ft-'):
                all_classes.add(c)
    print("  ft-* CSS classes:", sorted(all_classes)[:40])

    for sel in ['[class*="ft-card"]', 'article', '[class*="event"]', '[class*="agenda"]']:
        items = soup_agenda.select(sel)
        if items:
            print(f"\n  Found {len(items)} items with '{sel}'")
            for item in items[:2]:
                title_el = item.select_one('h2,h3,h4,[class*="title"]')
                date_el  = item.select_one('[class*="date"],[class*="data"],[datetime],[class*="when"]')
                link_el  = item.select_one('a[href]')
                loc_el   = item.select_one('[class*="loc"],[class*="place"],[class*="lloc"]')
                print(f"  title: {title_el.get_text(strip=True)[:60] if title_el else None}")
                print(f"  date : {date_el.get_text(strip=True)[:40] if date_el else None}")
                print(f"  loc  : {loc_el.get_text(strip=True)[:40] if loc_el else None}")
                print(f"  link : {link_el['href'][:80] if link_el else None}")
                print()
            break
