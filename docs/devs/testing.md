# Tests — agent_femturisme

Guia d'execució de tests automatitzats. Mapatge amb [tecnic.md §14](../client/tecnic.md).

---

## Comandes

```bash
# Instal·lar deps (inclou pytest)
python -m pip install -r requirements.txt

# Per defecte: API + unit (sense MySQL)
python -m pytest -v

# Només tests d'integració SQL (requereix MYSQL_* i repositories)
python -m pytest -m integration -v

# Tot excepte integració amb cobertura
python -m pytest -v --cov=app --cov-report=term-missing
```

Veure també [desenvolupament-local.md](desenvolupament-local.md) per venv i entorn Windows.

---

## Estructura

```text
tests/
├── conftest.py              # fixtures app, client, mock_tool_execute
├── helpers/
│   ├── sse.py               # parse_sse_events
│   └── env.py               # mysql_available()
├── api/
│   ├── test_chat.py         # API-01…API-04
│   └── test_health.py       # API-05
├── unit/
│   └── test_sse_parser.py
└── integration/sql/
    ├── test_experiences.py  # SQL-06
    ├── test_establishments.py  # SQL-01, SQL-02
    └── ...
```

---

## Tests API (tecnic §14.2)

| ID | Fitxer | Descripció |
|----|--------|------------|
| API-01 | `test_api_01_chat_empty_message_returns_400` | Missatge buit → 400 |
| API-02 | `test_api_02_chat_simple_message_sse_done` | Hola → SSE `done` |
| API-03 | `test_api_03_chat_catalog_tool_flow` | Rutes + mock tool → tool_call/result/done |
| API-04 | `test_api_04_session_reset_ok` | Reset sessió → `ok: true` |
| API-05 | `test_api_05_health_returns_200_json` | GET /health → 200, mysql/postgres not_configured |

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

Marcat `@pytest.mark.integration`. Es **salten** si no hi ha `MYSQL_HOST` + `MYSQL_USER` (o prefix `AGENT_`).

Quan existeixi el repository, el test s'executa contra MySQL staging.

---

## Variables d'entorn (integració)

```env
MYSQL_HOST=...
MYSQL_PORT=3306
MYSQL_USER=agent_read
MYSQL_PASSWORD=...
MYSQL_DATABASE=femturisme
```

O amb prefix `AGENT_MYSQL_*` (veure `app/config.py` quan s'implementi).

---

## Script auxiliar

```bash
python scripts/test_sql_queries.py --ping
```

Retorna 0 amb missatge «not implemented» fins que existeixi `app/db/connection.py`.

---

## Referències

- [desenvolupament-local.md](desenvolupament-local.md) — entorn Windows, venv, ports, MySQL remot
- [patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md) §8
- [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md) §8.3
- [checklist-entrega.md](checklist-entrega.md) DEV-201, DEV-603
