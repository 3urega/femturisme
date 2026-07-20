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

# API admin entitats (DEV-501; requereix POSTGRES_*)
python -m pytest tests/api/test_admin_entities.py -v -m integration

# API admin documents (DEV-502/503; requereix POSTGRES_*)
python -m pytest tests/api/test_admin_documents.py -v -m integration

# Pipeline indexació RAG (DEV-504; requereix POSTGRES_* + pymupdf)
python -m pytest tests/integration/rag/test_indexing_pipeline.py -v -m integration

# Cerca semàntica RAG (DEV-505; requereix POSTGRES_* + pymupdf)
python -m pytest tests/integration/rag/test_search_entity_knowledge.py -v -m integration

# UAT admin RAG (DEV-507; requereix POSTGRES_* + servidor en marxa per al script)
python -m pytest tests/integration/rag/test_rag_admin_lifecycle.py -v -m integration
python scripts/uat_rag_battery.py http://127.0.0.1:5010

# Hardening Fase 5 (issue #34): auth admin, reindex HTTP, lock, CLI ingest
python -m pytest tests/api/test_admin_auth.py -v -m integration
python -m pytest tests/integration/rag/test_reindex_http.py -v -m integration
python -m pytest tests/unit/test_indexing_lock.py -v
python scripts/ingest_pdf.py --list

# Storage S3 Supabase (issue #35)
python -m pytest tests/unit/test_document_storage.py -v
python -m pytest tests/integration/rag/test_s3_storage.py -v -m s3

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
│   ├── test_health.py       # API-05
│   ├── test_admin_entities.py  # DEV-501: CRUD /admin/api/entities
│   ├── test_admin_documents.py # DEV-502/503: upload/list/delete documents
│   ├── test_admin_auth.py        # issue #34: Bearer + cookie admin
│   └── test_admin_ui_routes.py # DEV-507: HTML /admin/guides*
├── fixtures/
│   └── sample-guide.pdf     # PDF mínim per tests upload
├── unit/
│   ├── test_mappers.py      # row_to_card, build_search_wrapper
│   ├── test_prompts.py      # build_system_prompt
│   ├── test_db_connection.py
│   ├── test_config.py
│   ├── test_document_storage.py  # issue #35: local + mock S3 backends
│   ├── test_sse_parser.py
│   └── test_chunking.py     # DEV-504: token chunking
└── integration/
    ├── sql/
    │   ├── test_establishments.py  # SQL-01, SQL-02
    │   ├── test_destinations.py    # SQL-04
    │   ├── test_events.py          # SQL-05
    │   ├── test_articles.py        # SQL-03
    │   ├── test_experiences.py     # SQL-06
    │   └── test_routes.py          # SQL-07
    ├── postgres/
    │   └── test_schema.py          # DEV-500: vector ext, tables, enums
    └── rag/
        ├── test_indexing_pipeline.py       # DEV-504: extract/chunk/embed pipeline
        ├── test_search_entity_knowledge.py # DEV-505: semantic search + smoke-test
        └── test_rag_admin_lifecycle.py     # DEV-507: delete cascades, failed search
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

## Tests API admin entitats (DEV-501)

| Test | Descripció |
|------|------------|
| `test_admin_create_and_get_entity` | POST crea entitat; GET detall coincideix |
| `test_admin_list_entities_includes_created` | GET llistat inclou entitat activa creada |
| `test_admin_delete_entity_returns_ok` | DELETE 200 `{ok:true}`; GET posterior 404 |
| `test_admin_rejects_invalid_entity_type` | POST amb `entity_type` invàlid → 400 |

Marcat `@pytest.mark.integration`. Requereix PostgreSQL amb schema aplicat (DEV-500). Auth: amb `ADMIN_API_TOKEN` buit (default dev), les rutes són obertes; en producció cal `Authorization: Bearer <token>`.

Smoke manual:

```bash
curl -s -X POST http://127.0.0.1:5010/admin/api/entities \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Museu prova\",\"entity_type\":\"museu\"}"
```

---

## Tests API admin documents (DEV-502, DEV-503)

| Test | Descripció |
|------|------------|
| `test_admin_upload_creates_pending_document_and_file` | POST multipart → 201, `status=pending`, fitxer a storage |
| `test_admin_list_and_get_document` | GET list (filtre `entity_id`) i GET detail |
| `test_admin_delete_document_removes_row_and_file` | DELETE 200; GET 404; directori eliminat |
| `test_admin_upload_rejects_missing_entity` | `entity_id` inexistent → 404 |
| `test_admin_upload_rejects_non_pdf` | fitxer no PDF → 400 |

Marcat `@pytest.mark.integration`. Els tests usen `tmp_path` com a `DOCUMENT_STORAGE_PATH` (no escriuen a `data/guides/` del repo). Cal una entitat creada prèviament via `/admin/api/entities`.

Smoke manual:

```bash
curl -s -X POST http://127.0.0.1:5010/admin/api/documents/upload \
  -F "file=@tests/fixtures/sample-guide.pdf" \
  -F "entity_id=<uuid>" \
  -F "title=Guia prova"
```

---

## Tests pipeline indexació RAG (DEV-504)

| Test | Descripció |
|------|------------|
| `test_pipeline_indexes_sample_pdf` | PDF fixture → `run()` amb mock embeddings → `status=indexed`, chunks a BD |
| `test_pipeline_fails_on_empty_pdf` | PDF sense text → `status=failed` + `error_message` |
| `test_reindex_replaces_chunks_and_increments_version` | Reindex incrementa `version` i reemplaça chunks |

Marcat `@pytest.mark.integration`. Mock d'embeddings obligatori (no cal `OPENAI_API_KEY`). Requereix `pymupdf` i `tiktoken` (`pip install -r requirements.txt`).

Smoke manual:

```bash
python -c "from app.services.indexing_pipeline import run; run('<doc_id>')"
curl -s -X POST http://127.0.0.1:5010/admin/api/documents/<doc_id>/reindex
```

---

## Tests cerca semàntica RAG (DEV-505)

| Test | Descripció |
|------|------------|
| `test_search_returns_chunks_for_indexed_entity` | `DocumentsRepository.search()` retorna chunks amb `content`/`metadata` |
| `test_search_filters_by_entity_id` | Entitat sense documents → `total=0` |
| `test_smoke_test_endpoint_returns_results` | `POST .../smoke-test` sobre doc `indexed` → 200 |
| `test_search_skips_non_indexed_documents` | Doc `pending` → search 0 resultats; smoke-test 400 |

Marcat `@pytest.mark.integration`. Mock d'embeddings obligatori (mateix patró que DEV-504).

Smoke manual:

```bash
curl -s -X POST http://127.0.0.1:5010/admin/api/documents/<doc_id>/smoke-test \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"on aparcar"}'
```

---

## Tests UAT admin RAG (DEV-507)

| Test | Descripció |
|------|------------|
| `test_delete_document_removes_chunks` | DELETE document → chunks eliminats |
| `test_delete_entity_cascades_documents` | DELETE entitat → documents CASCADE |
| `test_failed_document_excluded_from_search` | Doc `failed` → search `total=0` |

Script end-to-end (servidor Flask en marxa, `OPENAI_API_KEY` per indexació via upload):

```powershell
python main.py
python scripts/uat_rag_battery.py http://127.0.0.1:5010
```

Casos: UAT-RAG-01…06 (crear entitat, upload+indexed, smoke-test, reindex, delete doc, delete entity). Umbral: ≥5 PASS i ≥80%. Resultats opcionals: `uat_rag_battery_results.txt` (gitignore).

Panel admin manual (VS2 issue #32): `http://127.0.0.1:5010/admin/guides` — token admin a `sessionStorage` si `ADMIN_API_TOKEN` està configurat.

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
