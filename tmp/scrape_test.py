"""
Scraping feasibility test for femturisme.cat
Tests: plain request → browser headers → session with cookies → specific endpoints
"""
import sys
sys.path.insert(0, '/projects/restaurants/venv/lib/python3.11/site-packages')

import requests
from bs4 import BeautifulSoup
import json, time

HEADERS_BROWSER = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ca-ES,ca;q=0.9,es;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

URLS = {
    'home':          'https://www.femturisme.cat/',
    'experiences':   'https://www.femturisme.cat/ca/experiences',
    'routes':        'https://www.femturisme.cat/ca/rutes',
    'events':        'https://www.femturisme.cat/ca/agenda',
    'accommodations':'https://www.femturisme.cat/ca/allotjaments',
}

def test(label, url, session=None, extra_headers=None):
    caller = session or requests
    h = {**HEADERS_BROWSER, **(extra_headers or {})}
    try:
        r = caller.get(url, headers=h, timeout=15, allow_redirects=True)
        print(f"  [{r.status_code}] {label} — {url}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else '(no title)'
            # Count cards / items
            cards = soup.select('article, .card, [class*="card"], [class*="item"], [class*="result"]')
            links = [a['href'] for a in soup.select('a[href]') if 'femturisme' in a.get('href','')][:5]
            print(f"    Title   : {title}")
            print(f"    Cards   : {len(cards)} elements matched")
            print(f"    Links   : {links}")
            return soup
        else:
            print(f"    Body    : {r.text[:200]!r}")
            return None
    except Exception as e:
        print(f"  [ERR] {label} — {e}")
        return None

print("=" * 60)
print("TEST 1 — plain requests (no special headers)")
print("=" * 60)
r = requests.get('https://www.femturisme.cat/', timeout=15)
print(f"  Status: {r.status_code}")
print(f"  Body  : {r.text[:300]!r}")

print()
print("=" * 60)
print("TEST 2 — browser headers, individual URLs")
print("=" * 60)
soups = {}
for name, url in URLS.items():
    soup = test(name, url)
    if soup:
        soups[name] = soup
    time.sleep(1)

print()
print("=" * 60)
print("TEST 3 — session (persistent cookies), home first then sub-pages")
print("=" * 60)
session = requests.Session()
# Warm up with home page
test("home (warm-up)", 'https://www.femturisme.cat/', session)
time.sleep(1.5)
for name, url in list(URLS.items())[1:]:
    test(f"{name} (session)", url, session)
    time.sleep(1)

print()
print("=" * 60)
print("TEST 4 — inspect a successful page structure")
print("=" * 60)
if soups:
    name, soup = next(iter(soups.items()))
    print(f"  Analysing: {name}")
    # Print CSS classes on main containers
    main = soup.select_one('main, #main, .main, [role="main"]')
    if main:
        children = main.find_all(recursive=False)
        for c in children[:5]:
            print(f"    Tag: <{c.name}> classes={c.get('class','')}")
    # Look for JSON-LD or API calls
    scripts = soup.find_all('script', type='application/json')
    scripts += soup.find_all('script', attrs={'data-drupal-selector': True})
    print(f"  JSON scripts: {len(scripts)}")
    for s in scripts[:2]:
        print(f"    {s.get_text()[:200]!r}")
    # Any API endpoint hints
    api_hints = [s.string for s in soup.find_all('script') if s.string and '/api/' in s.string]
    print(f"  API hints in scripts: {len(api_hints)}")
    for h in api_hints[:3]:
        print(f"    {h[:300]!r}")
else:
    print("  No successful pages to analyse.")
