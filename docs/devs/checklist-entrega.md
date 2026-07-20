# Checklist d'entrega — agent_femturisme

**Progrés:** 56 / 90 completats · **Última actualització:** 2026-07-20

> Els agents marquen `- [x]` quan el criteri **Detect** es compleix. Veure [index.md](index.md).

**Referències:** [requeriments.md](../client/requeriments.md) · [funcional.md](../client/funcional.md) · [tecnic.md](../client/tecnic.md) · [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md)

---

## Fase 0 — Documentació i preparació equip

- [x] **DEV-001** — Domini de negoci documentat (`docs/client/dominio-femturisme-ca.md`, 6 buscadors + entitats)  
  *Detect:* fitxer existeix; distincions agenda/experiències/establiments
- [x] **DEV-002** — Presa de requeriments (RF, CA, Fases 1/2)  
  *Detect:* `docs/client/requeriments.md` complet
- [x] **DEV-003** — Disseny funcional (modes, fonts, tools)  
  *Detect:* `docs/client/funcional.md` complet
- [x] **DEV-004** — Disseny tècnic v2.1 (API, tools, fases, ADRs)  
  *Detect:* `docs/client/tecnic.md` complet
- [x] **DEV-005** — Docs d'arquitectura per codi nou  
  *Detect:* `docs/arquitectura/` (index, capes, patrons, estat actual)
- [x] **DEV-006** — `AGENTS.md` amb mapa de docs i constraints  
  *Detect:* fitxer a l'arrel del repo
- [x] **DEV-007** — Schema PostgreSQL agent documentat + DDL  
  *Detect:* `docs/postgre_schema.md` + `docs/schema-agent-postgres.sql`
- [x] **DEV-008** — Índex i checklist developers  
  *Detect:* `docs/devs/index.md` + aquest fitxer
- [x] **DEV-009** — Skills Cursor (plan → publish → kanban)  
  *Detect:* `.cursor/skills/plan-to-issues`, `publish-github-issues`, `kanban-board`
- [x] **DEV-010** — `sql-mapeo.md` complet (6 buscadors, SQL provada)  
  *Detect:* cap secció TBD; totes les queries amb casos prova *(2026-07-20: pytest 14/14, issue #26)*
- [x] **DEV-011** — Issues GitHub del roadmap publicades  
  *Detect:* `gh issue list --repo 3urega/femturisme` amb batch Fase 1–4 *(2026-07-13)*

---

## Fase A — Pre-requisits del client i ops

- [x] **DEV-020** — `docs/schema.sql` MySQL (estructura sense dades)  
  *Detect:* fitxer al repo; export client MariaDB 10.3.39 (2026-07-07)
- [ ] **DEV-021** — Usuari MySQL `agent_read` (SELECT only) creat  
  *Detect:* credencials a `.env` staging; connexió OK
- [ ] **DEV-022** — MySQL disponible per desenvolupament  
  *Detect:* query de prova des del servei agent. **Dev local:** dump importat a `127.0.0.1` ([desenvolupament-local.md §9](desenvolupament-local.md)). **Staging:** connexió remot quan el client obri xarxa.
- [ ] **DEV-023** — PostgreSQL staging amb extensió pgvector  
  *Detect:* `CREATE EXTENSION vector` OK; connexió des de Python. **Parcial (2026-07-20):** dev Supabase pooler + schema aplicat (#27); staging formal pendent
- [ ] **DEV-024** — Preguntes obertes Q-01…Q-08 resoltes amb client  
  *Detect:* `tecnic.md` §8.3 sense TBD crítics; `sql-mapeo.md` alimentat. **Parcial (2026-07-20):** estat per pregunta documentat; Q-04/Q-05/Q-08 pendents sign-off client
- [x] **DEV-025** — URLs canòniques per tipus de fitxa validades  
  *Detect:* documentades a `sql-mapeo.md` per buscador *(2026-07-20: §URLs + mappers.py; confirmació formal client pendent)*
- [x] **DEV-026** — Regles publicació / vigència / idioma definides  
  *Detect:* secció a `sql-mapeo.md` o domini §7 tancada *(2026-07-20: §1.4–6.4 + idioma §Metadades)*
- [ ] **DEV-027** — Xarxa staging PHP ↔ Python ↔ MySQL/PostgreSQL  
  *Detect:* proxy de prova funcional o document d'infra signat

---

## Fase 1 — Servei Python base (tecnic §15.1)

- [x] **DEV-100** — Dockerfile + docker-compose  
  *Detect:* `Dockerfile` + `docker-compose.yml` a l'arrel
- [x] **DEV-101** — `requirements.txt` complet (Flask, MySQL, PostgreSQL, pytest, embeddings…)  
  *Detect:* deps instal·lables; pytest a requirements.txt *(2026-07-08)*
- [x] **DEV-102** — `app/config.py` amb `AGENT_*`, `MYSQL_*`, `POSTGRES_*`, embeddings  
  *Detect:* variables llegides des de `.env.example`
- [x] **DEV-103** — `GET /health` (MySQL + PostgreSQL + servei)  
  *Detect:* endpoint retorna 200 amb estat de connexions *(2026-07-08)*
- [x] **DEV-104** — `POST /api/chat` amb SSE (`tool_call`, `tool_result`, `text_chunk`, `done`)  
  *Detect:* `app/routes/api.py` + smoke curl
- [x] **DEV-105** — `POST /api/session/reset`  
  *Detect:* endpoint + `ok: true`
- [x] **DEV-106** — Prototip bucle agent + multi-provider LLM  
  *Detect:* `agent_service.py` + `llm_service.py` funcionals
- [x] **DEV-107** — Widget JS demo (SSE + Markdown)  
  *Detect:* `app/static/js/chat.js`
- [ ] **DEV-108** — Desplegament staging Docker verificat  
  *Detect:* servei accessible al servidor staging; `/health` 200. **No** cal executar Docker al PC de dev (veure [desenvolupament-local.md](desenvolupament-local.md)).
- [x] **DEV-109** — `.env.example` sense secrets (plantilla completa)  
  *Detect:* fitxer documentat a tecnic §10.2

---

## Fase 2 — Exploració MySQL (tecnic §15.2, fase-2-tools-mysql-ca)

- [x] **DEV-200** — Estructura `app/db/` (`connection.py`, `mappers.py`, `repositories/`)  
  *Detect:* directoris creats segons arquitectura *(2026-07-08)*
- [x] **DEV-201** — `tests/conftest.py` + fixture Flask app  
  *Detect:* `pytest` arrenca sense errors; API-01…04 passen
- [x] **DEV-202** — Mapatge `search_establishments` a `sql-mapeo.md`  
  *Detect:* SQL + casos prova SQL-01/02 *(2026-07-13)*
- [x] **DEV-203** — Mapatge `search_articles`  
  *Detect:* SQL-03 *(2026-07-13)*
- [x] **DEV-204** — Mapatge `search_destinations`  
  *Detect:* SQL-04 *(2026-07-13)*
- [x] **DEV-205** — Mapatge `search_events`  
  *Detect:* SQL-05 *(2026-07-13)*
- [x] **DEV-206** — Mapatge `search_experiences`  
  *Detect:* SQL-06 *(2026-07-13)*
- [x] **DEV-207** — Mapatge `search_routes`  
  *Detect:* SQL-07 *(2026-07-13)*
- [x] **DEV-208** — Helper `row_to_card()` + wrapper JSON comú  
  *Detect:* `app/db/mappers.py`; contracte tecnic §6.13 *(2026-07-08)*

---

## Fase 3 — Sis buscadors MySQL (tecnic §15.3, fase-3-tools-mysql-ca)

Per cada buscador: **Repository + Tool refactor + test integració**. Sense `scraper.py`.

- [x] **DEV-301** — `ExperiencesRepository` + `search_experiences` MySQL + test  
  *Detect:* `tests/integration/sql/test_experiences.py` passa; tool sense import scraper *(2026-07-13)*
- [x] **DEV-302** — `EstablishmentsRepository` + `search_establishments` (dormir+menjar)  
  *Detect:* substitueix `search_accommodations`; test SQL-01/02 *(2026-07-13)*
- [x] **DEV-303** — `ArticlesRepository` + `search_articles`  
  *Detect:* test SQL-03 *(2026-07-13)*
- [x] **DEV-304** — `DestinationsRepository` + `search_destinations`  
  *Detect:* test SQL-04 *(2026-07-13)*
- [x] **DEV-305** — `EventsRepository` + `search_events`  
  *Detect:* test SQL-05; dates vigents *(2026-07-13)*
- [x] **DEV-306** — `RoutesRepository` + `search_routes`  
  *Detect:* test SQL-07 *(2026-07-13)*
- [x] **DEV-307** — Registre `ALL_TOOLS` amb 6 tools MySQL (noms objectiu)  
  *Detect:* `app/services/tools/__init__.py` sense tools legacy *(2026-07-13)*
- [x] **DEV-308** — Eliminar dependència `scraper.py` del catàleg  
  *Detect:* cap import scraper a tools de catàleg; fitxer eliminat o marcat deprecated *(2026-07-13)*
- [ ] **DEV-309** — Límits operatius (LIMIT 20, truncat 6 cards al model)  
  *Detect:* tecnic §6.14 implementat als repositories/servei; `meta.truncated` al wrapper  
  **Posposat fase final** *(2026-07-14):* només optimització de cost de tokens; LIMIT 20 ja actiu als repositories. Truncat a 6 cards abans del LLM → **Fase 9** (pre-entrega / prod), no bloqueja desenvolupament actual.
- [x] **DEV-310** — System prompt alineat amb 6 dominis + idiomes  
  *Detect:* prompt descriu tools correctes; regles CA-08 i lectura de `meta`; no menciona scraping *(2026-07-13)*

---

## Fase 4 — Integració web femturisme.cat (tecnic §15.4, T-PHP)

> **Posposada** *(2026-07-13):* no iniciar fins tancar qualitat de l'agent al xat Python de prova. Veure [plan-fase4-php-widget.md](plan-fase4-php-widget.md) § «Decisió: posposar Fase 4». Issues #18–#22 en backlog.

- [ ] **DEV-400** — Globus + panell xat al layout PHP (T-PHP-01)  
  *Detect:* widget visible staging
- [ ] **DEV-401** — Reverse proxy `/api/chat` i `/api/session/reset` (T-PHP-02)  
  *Detect:* same-origin; sense CORS al navegador
- [x] **DEV-402** — `page_context` al body del xat (T-PHP-03)  
  *Detect:* JSON enviat segons URL *(2026-07-14: API parseja `page_context` i injecta al prompt; issue #19)*
- [x] **DEV-403** — `agent_context` mode femturisme per defecte (T-PHP-04)  
  *Detect:* `mode: femturisme`, `entity_id: null` *(2026-07-14: default implícit; `mode: entitat` → 400/501; issue #19)*
- [ ] **DEV-404** — Botó «Nova conversa» (T-PHP-05)  
  *Detect:* crida session/reset
- [ ] **DEV-405** — Proves desktop + mòbil (T-PHP-06)  
  *Detect:* checklist PHP §14.5
- [ ] **DEV-406** — Headers SSE proxy (`X-Accel-Buffering: no`, timeout)  
  *Detect:* tecnic §4.8 aplicat a nginx/apache

---

## Fase 5 — Infra base coneixement entitats (tecnic §15.5)

*Infra es pot construir abans; **xat públic femturisme Fase 1 sense RAG** (requeriments §4).*

- [x] **DEV-500** — Schema PostgreSQL aplicat a staging  
  *Detect:* taules `entities`, `guide_documents`, `document_chunks` *(2026-07-20: Supabase dev + apply_postgres_schema.py, issue #27)*
- [x] **DEV-501** — API CRUD `/admin/api/entities`  
  *Detect:* tecnic §9.4; tests o smoke curl *(2026-07-20: EntitiesRepository + admin blueprint + 4 tests integration, issue #28)*
- [x] **DEV-502** — API documents (upload, list, reindex, delete, smoke-test)  
  *Detect:* tecnic §9.5–9.6 *(2026-07-20: upload/list/detail/delete admin + 5 tests; reindex/smoke-test → issue #33)*
- [x] **DEV-503** — Emmagatzematge PDF `data/guides/{doc_id}/original.pdf`  
  *Detect:* pujada + fitxer a disc *(2026-07-20: document_storage.py + issue #29)*
- [x] **DEV-504** — Pipeline indexació (extract → chunk → embed → indexed)  
  *Detect:* estats BD pending…indexed; failed amb error_message *(2026-07-20: indexing_pipeline + reindex endpoint + 3 tests integration, issue #33)*
- [x] **DEV-505** — `DocumentsRepository` + `search_entity_knowledge`  
  *Detect:* tool registrada; cerca per `entity_id` *(2026-07-20: DocumentsRepository.search + tool + smoke-test + 4 tests integration, issue #31)*
- [ ] **DEV-506** — Gestor entitats + documental UI backend PHP (RF-13)  
  *Detect:* CRUD entitats i documents des del backend femturisme
- [x] **DEV-507** — UAT intern RAG (entitats prova + PDF indexats)  
  *Detect:* tecnic §14.4 admin; smoke-test OK *(2026-07-20: uat_rag_battery.py + test_rag_admin_lifecycle.py, issue #32 VS1)*

---

## Fase 6 — Entrega Fase producte 1 (assistent femturisme, sense RAG públic)

- [x] **DEV-600** — Mode femturisme: només 6 tools MySQL exposades al LLM  
  *Detect:* `search_entity_knowledge` no invocable des del xat públic *(2026-07-14: `CATALOG_TOOLS` al agent + prompt; `search_local_knowledge` fora del LLM)*
- [x] **DEV-601** — Idiomes ca / es / en / fr (RF-10)  
  *Detect:* respostes coherents en proves manual UAT *(2026-07-14: detecció per torn, injecció `lang` a tools, prompt fr; UAT 7/8 — `scripts/uat_languages_battery.py`)*
- [x] **DEV-602** — Rate limiting + logging mínim (tecnic §12–13)  
  *Detect:* logs amb session_id, latència SQL *(2026-07-14: `rate_limit.py`, `request_logging.py`, 429 /api/chat; issue #23)*
- [x] **DEV-603** — Tests API (API-01…API-04)  
  *Detect:* tecnic §14.2 passen *(2026-07-14: `pytest tests/api/` 5/5)*
- [x] **DEV-604** — UAT catàleg (12 proves, 2 per domini)  
  *Detect:* tecnic §14.3 lot Catàleg ≥80% routing *(2026-07-14: 12/12 routing 100%, script `scripts/uat_catalog_battery.py`)*
- [x] **DEV-605** — **CA-01…CA-09** verificats (requeriments §12)  
  *Detect:* matriu CA amb evidència (staging) *(2026-07-14: 9/9 OK al chat Flask demo — `docs/devs/ca-matrix-fase1.md`; issue #25)*
- [ ] **DEV-606** — Sign-off client Fase 1 staging  
  *Detect:* acceptació formal documentada
- [ ] **DEV-607** — Desplegament producció Fase 1 (sense RAG al xat públic)  
  *Detect:* femturisme.cat xat actiu; checklist tecnic §11.2

---

## Fase 7 — Fase producte 2 (entitats + RAG condicional)

- [ ] **DEV-700** — `entity_id` a fitxes MySQL (Q-08) + camp a card JSON  
  *Detect:* repository inclou `entity_id` quan existeix al CMS
- [ ] **DEV-701** — Filtratge tools per `agent_context.mode`  
  *Detect:* mode entitat només RAG; mode femturisme 6 tools + RAG condicional
- [ ] **DEV-702** — Flux catàleg → RAG només si `results[].entity_id` (§5.6)  
  *Detect:* sense entity_id no hi ha crida `search_entity_knowledge`
- [ ] **DEV-703** — Widget/xat propi per entitat (`mode: entitat`)  
  *Detect:* agent_context amb entity_id fix
- [ ] **DEV-704** — Un parell de fitxes prova amb entitat associada  
  *Detect:* mapatge manual CMS documentat
- [ ] **DEV-705** — UAT mode entitat (8 proves)  
  *Detect:* tecnic §14.3; sense fuites de catàleg aliè
- [ ] **DEV-706** — UAT mixtes catàleg + RAG condicional  
  *Detect:* tecnic §14.3 lot Mixtes
- [ ] **DEV-707** — Sign-off client Fase 2  
  *Detect:* acceptació formal

---

## Fase 8 — Ops, seguretat i producció completa

- [ ] **DEV-800** — Secrets `.env` producció (mai al repo)  
  *Detect:* checklist tecnic §10–12
- [ ] **DEV-801** — Admin documental no públic (VPN/IP, auth)  
  *Detect:* tecnic §12.1
- [ ] **DEV-802** — Backups PostgreSQL + `data/guides/`  
  *Detect:* runbook §13.2
- [ ] **DEV-803** — Runbooks incidències (PDF failed, MySQL down, LLM down…)  
  *Detect:* tecnic §13.3
- [ ] **DEV-804** — KPIs monitorització inicial (requeriments §13)  
  *Detect:* mètriques recollides post-desplegament
- [ ] **DEV-805** — Decisions pendents P-01…P-06 tancades o documentades  
  *Detect:* tecnic §16.1 actualitzat

---

## Fase 9 — Entrega final al client

> **DEV-309 (truncat 6 cards):** posposat aquí — optimització de cost de tokens abans de producció; veure Fase 3 DEV-309.

- [ ] **DEV-900** — Documentació d'operació lliurada (desplegament, .env, runbooks)  
  *Detect:* paquet docs per ops/client
- [ ] **DEV-901** — Formació / handover equip femturisme (admin PDFs, entitats)  
  *Detect:* sessió registrada o guia d'usuari admin
- [ ] **DEV-902** — Codi en repositori `3urega/femturisme` taggejat (release)  
  *Detect:* tag semver + changelog
- [ ] **DEV-903** — Proves de regressió post-producció  
  *Detect:* UAT smoke en prod
- [ ] **DEV-904** — Tancament formal projecte / acta de recepció  
  *Detect:* signatura client

---

## Matriu RF → fases (referència ràpida)

| RF | Descripció breu | Fase checklist |
|----|-----------------|----------------|
| RF-01…RF-11 | Xat, catàleg, context, idiomes, enllaços | 3, 4, 6 |
| RF-12 | Escalabilitat tools | 3, 7 |
| RF-13 | Gestió documental entitat | 5, 7 |
| RF-14 | Context operatiu (modes) | 6, 7 |
| RF-15 | entity_id + RAG condicional | 7 |

---

## Historial de canvis

| Data | Canvis |
|------|--------|
| 2026-07-20 | DEV-500 tancat (issue #27); schema RAG Supabase pgvector + SSL pooler |
| 2026-07-20 | DEV-010, DEV-025, DEV-026 tancats (issue #26); sql-mapeo validat pytest 14/14 |
| 2026-07-14 | Fase 6 pre-entrega parcial (DEV-602, DEV-605); Fase 5 batch publicat |
| 2026-07-03 | Creació inicial des de docs/client (requeriments, funcional, tecnic, domini) |
