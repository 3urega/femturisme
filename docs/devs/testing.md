# Tests — agent_femturisme

Guia d'execució de tests automatitzats. Mapatge amb [tecnic.md §14](../client/tecnic.md).

---

## Comandes

```bash
# Instal·lar deps (inclou pytest)
python -m pip install -r requirements.txt

# Per defecte: API + unit (sense MySQL)
python -m pytest -v

# Només tests d'integració (requereix MYSQL_* o POSTGRES_*)
python -m pytest -m integration -v

# Schema PostgreSQL (DEV-500; requereix POSTGRES_* + apply_postgres_schema.py)
python scripts/apply_postgres_schema.py
python -m pytest tests/integration/postgres/test_schema.py -v -m integration

# Tot excepte integració amb cobertura
python -m pytest -v --cov=app --cov-report=term-missing
```

Veure també [desenvolupament-local.md](desenvolupament-local.md) per venv i entorn Windows.

---

## Estructura

```text
tests/
├── conftest.py              # load_dotenv + fixtures app, client, mock_tool_execute
├── helpers/
│   ├── sse.py               # parse_sse_events
│   └── env.py               # mysql_available(), postgres_available()
├── api/
│   ├── test_chat.py         # API-01…API-04
│   └── test_health.py       # API-05
├── unit/
│   ├── test_mappers.py      # row_to_card, build_search_wrapper
│   ├── test_prompts.py      # build_system_prompt
│   ├── test_db_connection.py
│   ├── test_config.py
│   └── test_sse_parser.py
└── integration/
    ├── sql/
    │   ├── test_establishments.py  # SQL-01, SQL-02
    │   ├── test_destinations.py    # SQL-04
    │   ├── test_events.py          # SQL-05
    │   ├── test_articles.py        # SQL-03
    │   ├── test_experiences.py     # SQL-06
    │   └── test_routes.py          # SQL-07
    └── postgres/
        └── test_schema.py          # DEV-500: vector ext, tables, enums
```

---

## Tests PostgreSQL schema (DEV-500)

| Test | Descripció |
|------|------------|
| `test_vector_extension_installed` | Extensió `pgvector` activa |
| `test_rag_tables_exist` | Taules `entities`, `guide_documents`, `document_chunks` |
| `test_enum_types_exist` | ENUMs `entity_type`, `guide_document_status` |
| `test_embedding_column_is_vector_1536` | Columna `embedding` és `vector(1536)` |

Marcat `@pytest.mark.integration`. Es **salten** sense `POSTGRES_HOST` + `POSTGRES_USER`. Cal executar abans `python scripts/apply_postgres_schema.py` contra instància cloud amb pgvector. Supabase: usa pooler `:6543` si el port directe `:5432` està bloquejat (veure [desenvolupament-local.md](desenvolupament-local.md) §7.4).

```env
POSTGRES_HOST=aws-0-eu-central-1.pooler.supabase.com
POSTGRES_PORT=6543
POSTGRES_USER=postgres.<project-ref>
POSTGRES_PASSWORD=...
POSTGRES_DATABASE=postgres
# POSTGRES_SSLMODE=require  # auto per hosts supabase.co / neon.tech
```

---

## Tests API (tecnic §14.2)

| ID | Fitxer | Descripció |
|----|--------|------------|
| API-01 | `test_api_01_chat_empty_message_returns_400` | Missatge buit → 400 |
| API-02 | `test_api_02_chat_simple_message_sse_done` | Hola → SSE `done` |
| API-03 | `test_api_03_chat_catalog_tool_flow` | Rutes + mock tool → tool_call/result/done |
| API-04 | `test_api_04_session_reset_ok` | Reset sessió → `ok: true` |
| API-05 | `test_api_05_health_returns_200_json` | GET /health → 200; mysql `ok` o `not_configured` |

Usa `LLM_PROVIDER=dummy` via `TestingConfig`. Això **no afecta** el teu `.env` quan executes `python main.py` amb la API key del client.

---

## Tests SQL (tecnic §14.1)

| ID | Fitxer | Paràmetres |
|----|--------|------------|
| SQL-01 | `test_establishments_girona_hotel` | Girona, hotel |
| SQL-02 | `test_establishments_pals_restaurant` | Pals, restaurant |
| SQL-03 | `test_articles_parc_cadi` | topic Parc Natural Cadí |
| SQL-04 | `test_destinations_besalu` | Besalú |
| SQL-05 | `test_events_emporda_weekend` | Empordà + dates |
| SQL-06 | `test_experiences_olvan` | Olvan |
| SQL-07 | `test_routes_emporda_foot` | Empordà, A peu |

Marcat `@pytest.mark.integration`. Es **salten** si no hi ha `MYSQL_HOST` + `MYSQL_USER` (o prefix `AGENT_`). `conftest.py` carrega `.env` via `load_dotenv()` abans d'importar l'app.

**Batch 1 verificat** (#11): SQL-01/02/04/05 contra MySQL Railway (còpia producció).

**Batch 2 verificat** (#17): SQL-03/06/07 contra MySQL Railway — articles, experiències promocionals i rutes.

---

## Variables d'entorn (integració)

Veure [desenvolupament-local.md](desenvolupament-local.md) §7.3 — **dev Railway** (TCP proxy) o prod client.

```env
MYSQL_HOST=thomas.proxy.rlwy.net   # exemple Railway TCP proxy
MYSQL_PORT=49223                   # port assignat per Railway
MYSQL_USER=root
MYSQL_PASSWORD=...
MYSQL_DATABASE=railway
```

O amb prefix `AGENT_MYSQL_*` (veure `app/config.py`).

---

## Script auxiliar

```bash
python scripts/test_sql_queries.py --ping
```

Carrega `.env` i comprova connectivitat MySQL/PostgreSQL (`ok`, `not_configured` o `error`).

---

## Referències

- [desenvolupament-local.md](desenvolupament-local.md) — entorn Windows, venv, ports, MySQL remot
- [patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md) §8
- [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md) §8.3
- [checklist-entrega.md](checklist-entrega.md) DEV-201, DEV-603
