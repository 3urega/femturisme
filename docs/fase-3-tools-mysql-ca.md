# Fase 3 — Tools de catàleg amb MySQL

> **v1.1:** implementar **6 repositoris** (`EstablishmentsRepository`, `ArticlesRepository`, `DestinationsRepository`, `RoutesRepository`, `EventsRepository`, `ExperiencesRepository`). Domini: [dominio-femturisme-ca.md](dominio-femturisme-ca.md). El prototip actual té 4 tools + scraping.

**Guia per al developer.** Document operatiu: què fer, en quin ordre, quins fitxers tocar, com provar-ho.

**Prerequisit obligatori:** Fase 2 tancada → existeix `docs/sql-mapeo.md` amb la SQL **real** (noms de taules, JOINs, casos de prova). Sense això no es pot programar la Fase 3.

---

## 1. Què has de fer (una frase)

Substituir el **scraping HTML** per **consultes MySQL parametritzades** per als **6 buscadors**, mantenint format JSON de resposta coherent amb [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) §5.

---

## 2. Com funciona avui vs com ha de quedar

### Avui (scraping)

```
LLM crida search_experiences({ destination: "Berguedà" })
    → experiences.py execute()
    → fetch_page('/ofertes', { ubicacio: "Berguedà" })
    → BeautifulSoup extreu cards HTML
    → json.dumps({ destination, results: [...] })
```

Fitxer actual: `app/services/tools/experiences.py` (i equivalents per accommodations, events, routes).

### Objectiu (MySQL)

```
LLM crida search_experiences({ destination: "Berguedà" })   ← igual
    → experiences.py execute()                                ← mateix fitxer, canvia el cos
    → ExperiencesRepository.search(destination=..., category=...)
    → MySQL SELECT parametritzat (de sql-mapeo.md)
    → row_to_card() per cada fila
    → json.dumps({ destination, results: [...] })           ← mateix shape JSON
```

**El LLM no veu MySQL.** Només ve el SCHEMA de la tool i el JSON que retorna `execute()`.

---

## 3. Les 4 tools (mapa)

| Tool | Fitxer actual | Repositori nou | Paràmetres LLM |
|------|---------------|----------------|----------------|
| `search_experiences` | `app/services/tools/experiences.py` | `app/db/repositories/experiences.py` | `destination`, `category?` |
| `search_accommodations` | `app/services/tools/accommodations.py` | `app/db/repositories/accommodations.py` | `destination`, `type?` |
| `search_events` | `app/services/tools/events.py` | `app/db/repositories/events.py` | `destination`, `date_from?`, `date_to?` |
| `search_routes` | `app/services/tools/routes_tool.py` | `app/db/repositories/routes.py` | `destination`, `type?` |

**No creïs tools noves.** No canviïs noms al `ALL_TOOLS`. Refactoritza `execute()` dins els fitxers existents.

---

## 4. Fitxers a crear i modificar

```
agent_femturisme/
├── app/
│   ├── config.py                          ← MODIFICAR: MYSQL_*
│   ├── db/
│   │   ├── __init__.py                    ← CREAR
│   │   ├── connection.py                  ← CREAR: pool MySQL
│   │   ├── mappers.py                     ← CREAR: row → card JSON
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── experiences.py             ← CREAR
│   │       ├── accommodations.py
│   │       ├── events.py
│   │       └── routes.py
│   └── services/tools/
│       ├── experiences.py                 ← MODIFICAR: cridar repo, no scraper
│       ├── accommodations.py
│       ├── events.py
│       └── routes_tool.py
├── tests/sql/
│   ├── test_experiences.py                ← CREAR
│   └── ...
├── scripts/
│   └── test_sql_queries.py                ← CREAR: prova manual ràpida
└── docs/sql-mapeo.md                      ← JA EXISTEIX (Fase 2)
```

---

## 5. Ordre d'implementació (no facis les 4 a la vegada)

| Pas | Què | Com saps que està bé |
|-----|-----|----------------------|
| **3.0** | Connexió MySQL | `python scripts/test_sql_queries.py --ping` → OK |
| **3.1** | `search_experiences` sola | Test SQL passa + xat respon amb dades MySQL |
| **3.2** | `search_accommodations` | Idem |
| **3.3** | `search_events` | Idem |
| **3.4** | `search_routes` | Idem |
| **3.5** | Eliminar dependència scraper de les 4 tools | Cap import de `scraper.py` a experiences/accommodations/events/routes |

Implementa **una tool completa** abans d'obrir la següent. És la plantilla per a les altres.

---

## 6. Pas 3.0 — Connexió MySQL

### 6.1 Variables `.env`

```bash
MYSQL_HOST=staging-mysql.femturisme.internal
MYSQL_PORT=3306
MYSQL_USER=agent_read
MYSQL_PASSWORD=...
MYSQL_DATABASE=femturisme
```

### 6.2 `app/config.py` — afegir

```python
MYSQL_HOST     = _env('MYSQL_HOST')
MYSQL_PORT     = int(_env('MYSQL_PORT', 3306))
MYSQL_USER     = _env('MYSQL_USER')
MYSQL_PASSWORD = _env('MYSQL_PASSWORD')
MYSQL_DATABASE = _env('MYSQL_DATABASE')
```

### 6.3 `app/db/connection.py` — exemple mínim

```python
"""Pool MySQL read-only. Usar sempre placeholders (%s), mai concatenar SQL."""
from contextlib import contextmanager
import pymysql
from flask import current_app

_pool = None

def init_app(app):
    global _pool
    # Pool simple; es pot canviar per SQLAlchemy si cal
    app.mysql_config = {
        'host': app.config['MYSQL_HOST'],
        'port': app.config['MYSQL_PORT'],
        'user': app.config['MYSQL_USER'],
        'password': app.config['MYSQL_PASSWORD'],
        'database': app.config['MYSQL_DATABASE'],
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': 5,
        'read_timeout': 10,
    }

@contextmanager
def get_cursor():
    cfg = current_app.mysql_config
    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()  # read-only; no fa mal
    finally:
        conn.close()
```

Registrar a `app/__init__.py`:

```python
from app.db.connection import init_app as init_mysql
init_mysql(app)
```

### 6.4 Prova ràpida — `scripts/test_sql_queries.py`

```bash
python scripts/test_sql_queries.py --ping
# Esperat: MySQL OK, 1 row
```

```python
# scripts/test_sql_queries.py (fragment)
if args.ping:
    with app.app_context():
        with get_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            print(cur.fetchone())
```

---

## 7. Pas 3.1 — Exemple complet: `search_experiences`

Aquest exemple usa noms de columna **inventats** (`ofertes`, `titulo_ca`…). **Substitueix-los** pels de `docs/sql-mapeo.md` quan la Fase 2 estigui feta.

### 7.1 Contracte JSON (no canviar)

Cada card ha de tenir aquests camps (el LLM ja està entrenat amb scraping que retornava això):

```json
{
  "destination": "Berguedà",
  "category": "Familiar",
  "total": 12,
  "results": [
    {
      "id": "12345",
      "type": "oferta",
      "title": "Ruta familiar pel Pedraforca",
      "location": "Gósol, Berguedà",
      "description": "Text curt de la fitxa…",
      "url": "https://www.femturisme.cat/ofertes/ruta-familiar-pedraforca",
      "image": "https://www.femturisme.cat/media/…/foto.jpg",
      "date": null
    }
  ],
  "error": null
}
```

### 7.2 SQL (documentada a sql-mapeo.md) — plantilla

```sql
-- PLACEHOLDER: copiar SQL final de sql-mapeo.md § search_experiences
SELECT
    o.id,
    o.tipus       AS type,
    o.titol_ca    AS title,
    u.nom         AS location,
    o.descripcio  AS description,
    o.slug        AS slug,
    o.imatge_url  AS image,
    NULL          AS event_date
FROM ofertes o
JOIN ubicacions u ON u.id = o.ubicacio_id
WHERE o.publicat = 1
  AND o.eliminat = 0
  AND (
        u.nom LIKE CONCAT('%', :destination, '%')
     OR u.comarca LIKE CONCAT('%', :destination, '%')
  )
  AND (:category IS NULL OR o.categoria = :category)
ORDER BY o.data_modificacio DESC
LIMIT 20;
```

**Important:** a Python usa `%s` (pymysql), no `:destination`:

```python
params = (destination, category, category)  # category repetit per IS NULL trick, o SQL separada
```

### 7.3 `app/db/mappers.py`

```python
BASE_URL = "https://www.femturisme.cat"

def build_url(path_prefix: str, slug: str | None) -> str | None:
    if not slug:
        return None
    return f"{BASE_URL}{path_prefix}/{slug}"

def row_to_experience_card(row: dict) -> dict:
    return {
        "id":          str(row["id"]) if row.get("id") is not None else None,
        "type":        row.get("type"),
        "title":       row.get("title") or "",
        "location":    row.get("location"),
        "description": row.get("description"),
        "url":         build_url("/ofertes", row.get("slug")),
        "image":       row.get("image"),
        "date":        row.get("event_date"),
    }
```

La funció `build_url` ha coincidir amb com construeix la web (validar a Fase 2 amb URLs reals).

### 7.4 `app/db/repositories/experiences.py`

```python
from app.db.connection import get_cursor
from app.db.mappers import row_to_experience_card

# Copiar SQL literal de sql-mapeo.md
_SEARCH_SQL = """
SELECT ... FROM ... WHERE ... LIMIT 20
"""

def search(destination: str, category: str | None = None, limit: int = 20) -> dict:
    destination = (destination or "").strip()
    if not destination:
        return {"results": [], "total": 0}

    params = [destination, destination]  # ajustar segons SQL real
    if category:
        params.append(category)

    with get_cursor() as cur:
        cur.execute(_SEARCH_SQL, params)
        rows = cur.fetchall()

    cards = [row_to_experience_card(r) for r in rows if r.get("title")]
    return {
        "results": cards[:limit],
        "total": len(cards),  # o COUNT(*) separat si sql-mapeo ho defineix
    }
```

### 7.5 Refactor `app/services/tools/experiences.py`

**Abans:** importa `fetch_page`, `extract_cards` de `scraper.py`.

**Després:**

```python
import json
from app.db.repositories import experiences as exp_repo

SCHEMA = {
    # NO CANVIAR name, description, input_schema llevat que Fase 2 digui el contrari
    'name': 'search_experiences',
    ...
}

def execute(tool_input: dict) -> str:
    destination = tool_input.get('destination', '').strip()
    category    = tool_input.get('category')

    try:
        data = exp_repo.search(destination=destination, category=category)
        return json.dumps({
            'destination': destination,
            'category':    category,
            'total':       data['total'],
            'results':     data['results'],
            'error':       None,
        }, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({
            'destination': destination,
            'category':    category,
            'total':       None,
            'results':     [],
            'error':       f'MySQL error: {exc}',
        }, ensure_ascii=False)
```

**El SCHEMA no canvia** → el LLM segueix cridant la tool igual.

---

## 8. Com provar (sense esperar al xat)

### 8.1 Script directe al repositori

```bash
flask shell
>>> from app.db.repositories.experiences import search
>>> search("Berguedà", category="Familiar")
```

Comprova: `len(results) > 0`, cada resultat té `title` i `url` vàlid.

### 8.2 Comparar scraping vs MySQL (durant la migració)

Amb la mateixa `destination`, les llistes no han de ser idèntiques fila a fila, però:

- Mateix ordre de magnitud de resultats
- URLs obren fitxes reals a femturisme.cat
- Títols coherents amb la comarca

### 8.3 Test automatitzat — `tests/sql/test_experiences.py`

```python
import pytest
from app.db.repositories.experiences import search

@pytest.mark.integration
def test_experiences_bergueda(app):
    """Cas documentat a sql-mapeo.md"""
    with app.app_context():
        data = search(destination="Berguedà", category="Familiar")
    assert data["total"] >= 1
    assert data["results"][0]["title"]
    assert data["results"][0]["url"].startswith("https://www.femturisme.cat/")
```

Executar (amb MySQL staging accessible):

```bash
pytest tests/sql/test_experiences.py -m integration
```

### 8.4 Prova via agent (xat)

```bash
# .env: LLM_PROVIDER=anthropic (o dummy amb tool forçada)
flask run
```

Al navegador, pregunta: *«Quines activitats familiars hi ha al Berguedà?»*

Al log/SSE ha d'aparèixer:

```json
{ "type": "tool_call", "tool": "search_experiences", "input": { "destination": "Berguedà", "category": "Familiar" } }
```

I la resposta ha de citar títols que existeixen a MySQL.

---

## 9. Repetir per les altres 3 tools

Per cada tool, el patró és **idèntic**:

1. Copiar SQL de `sql-mapeo.md` → `_SEARCH_SQL` al repositori.
2. Crear `row_to_*_card()` si el mapatge difereix (events poden tenir `date`).
3. Refactor `execute()` → crida repo, mateix wrapper JSON.
4. Test a `tests/sql/test_*.py` amb casos de sql-mapeo.md.

### Particularitats

| Tool | Extra respecte experiences |
|------|----------------------------|
| `search_events` | Filtrar per `date_from` / `date_to`; omplir camp `date` a la card |
| `search_accommodations` | Paràmetre `type` (hotel, càmping…); URL prefix `/on-dormir` o el que digui sql-mapeo |
| `search_routes` | Paràmetre `type`; URL prefix `/rutes` |

---

## 10. Què NO has de fer

| Error comú | Per què |
|------------|---------|
| Canviar el nom de la tool al SCHEMA | El prompt i proves trencades |
| Concatenar strings a la SQL (`f"WHERE nom = '{destination}'"`) | SQL injection |
| Exposar SQL o taules al LLM | Fora d'arquitectura |
| Fer text-to-SQL | Veure `plan-integracion-ca.md` Annex D |
| Escriure a MySQL | Usuari `agent_read` només SELECT |
| Importar `scraper.py` després del refactor | Codi mort; confusió |

---

## 11. Definition of done (Fase 3 tancada)

- [ ] `app/db/connection.py` operatiu; `--ping` OK a staging.
- [ ] 4 repositoris implementats segons `sql-mapeo.md`.
- [ ] 4 `execute()` refactoritzats; **cap** usa scraping per catàleg.
- [ ] Tests `tests/sql/` passen contra MySQL staging (mínim 1 cas per tool).
- [ ] `pytest` + prova manual xat per cada tool.
- [ ] URLs de resultats obren fitxa correcta al navegador (spot check 3 URLs per tool).
- [ ] PR revisat amb SQL de sql-mapeo.md al costat del codi.

---

## 12. Si et bloqueges

| Situació | Acció |
|----------|-------|
| No existeix `sql-mapeo.md` | **Atura't.** Fes Fase 2 primer. |
| No saps quina taula | Obre `docs/schema.sql` + DBeaver; demana al mantenedor PHP |
| La SQL retorna 0 files però la web en té | Revisa regles `publicat`, JOIN ubicació, encoding |
| La SQL és lenta (>2s) | `EXPLAIN`; índexs; redueix LIMIT |
| El LLM no crida la tool | Problema de SCHEMA/descripció, no de MySQL — no és Fase 3 |
| Error connexió MySQL | Fase 0/1: firewall, credencials, host des del contenidor Docker |

---

## 13. Referències al repo

| Què | On |
|-----|-----|
| Registre tools | `app/services/tools/__init__.py` |
| Bucle agent | `app/services/agent_service.py` → `execute_tool()` |
| Scraping actual (referència format JSON) | `app/services/tools/scraper.py` → `extract_cards()` |
| SQL especificació | `docs/sql-mapeo.md` (Fase 2) |
| Pla complet Fase 3 (1 línia) | `plan-integracion-ca.md` §7 |
