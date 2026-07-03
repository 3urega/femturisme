# Pla d'integració

> **Actualització v1.1 (2026-06-28):** el catàleg MySQL passa de **4 a 6 buscadors** (+ guies PDF). Font de veritat del negoci: **[dominio-femturisme-ca.md](dominio-femturisme-ca.md)**. Especificacions client: [document-funcional-client-ca.md](document-funcional-client-ca.md), [especificacio-funcional-ca.md](especificacio-funcional-ca.md), [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md). Annex A d'aquest pla reflecteix parcialment el model antic on encara diu «4 tools» en alguns paràgrafs — usar el domini com a referència.

Pla mestre per fases. Objectiu: **xat integrat a femturisme.cat** alimentat per un **servei agent Python** amb accés **MySQL** (catàleg) i **vector store** (guies PDF), en un **únic widget** per a l'usuari.

Arquitectura de l'agent (bucle tool use, LLM, SSE): document tècnic `agente.md`.

---

## Índex

1. [Visió i arquitectura objectiu](#1-visió-i-arquitectura-objectiu)
2. [Principis](#2-principis)
3. [Mapa de fases](#3-mapa-de-fases)
4. [Fase 0 — Infraestructura i accessos](#fase-0)
5. [Fase 1 — Servei Python al servidor](#fase-1)
6. [Fase 2 — Exploració MySQL i disseny de queries](#fase-2)
7. [Fase 3 — Tools de catàleg amb MySQL](#fase-3)
8. [Fase 4 — Widget a femturisme.cat](#fase-4)
9. [Fase 5 — Ingesta de PDFs i vector store](#fase-5)
10. [Fase 6 — Tool RAG (guies municipals)](#fase-6)
11. [Fase 7 — Xat unificat](#fase-7)
12. [Fase 8 — Producció i operacions](#fase-8)
13. [Criteris d'èxit](#13-criteris-dèxit)
14. [Riscos i decisions pendents](#14-riscos-i-decisions-pendents)
15. [Annex A — Checklist SQL per tool](#15-annex-a--checklist-sql-per-tool)
16. [Annex B — Contracte JSON cap al LLM](#16-annex-b--contracte-json-cap-al-llm)
17. [Annex C — Estructura de carpetes](#17-annex-c--estructura-de-carpetes)
18. [Annex D — Tools parametritzades vs text-to-SQL](#anexo-d)

---

## 1. Visió i arquitectura objectiu

```
┌────────────────────────────────────────────────────────────────────────┐
│ femturisme.cat (PHP) — frontend públic                                   │
│  • Globus flotant + panell de xat (JS/CSS al layout global)            │
│  • page_context: secció, ubicació, municipi (des de la URL)            │
│  • NO inclou pujada de PDFs ni administració de l'agent                │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ POST /api/chat  (SSE, mateix domini via proxy)
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Servei agent — Python (servidor dedicat / contenidor)                  │
│  • API xat: AgentService + LLM + SSE                                   │
│  • Panell admin intern (Fase 5): /admin/guides — pujada i estat PDFs   │
│  • Tools catàleg → repositoris MySQL (només lectura)                   │
│  • Tools guies     → vector store (PDFs indexats)                      │
└───────────────┬───────────────────────────────┬────────────────────────┘
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ MySQL femturisme           │   │ Vector store + BD agent     │
│ experiències, agenda,      │   │ chunks, embeddings,         │
│ allotjaments, rutes…       │   │ guide_documents (estat PDF) │
└───────────────────────────┘   └───────────────────────────┘
```

**Dos frontends, dos rols:**

| Frontend | On viu | Qui el fa servir | Funció |
|----------|--------|------------------|--------|
| **Widget de xat** | femturisme.cat (PHP + JS) | Visitants de la web | Conversar amb l'agent |
| **Panell admin PDFs** | Servei Python (`/admin/guides`) | Equip femturisme (intern) | Pujar guies, veure estat d'indexació |

**Un sol xat** per a l'usuari final. El LLM tria tools de catàleg, de guies PDF, o ambdues segons la pregunta.

---

## 2. Principis

1. **Reutilitzar l'agent Python** — `AgentService`, `llm_service`, patró SCHEMA + `execute()`.
2. **MySQL només lectura** des del servei Python; l'agent no escriu a la BD.
3. **Queries dissenyades per al LLM** — camps, filtres i límits pensats per a les tools, no per replicar pantalles PHP. Decisió detallada: [Annex D](#anexo-d).
4. **Contracte JSON estable** entre repositoris i LLM (Annex B).
5. **Catàleg i guies PDF** — fonts i tools distintes; mateix endpoint `/api/chat`.
6. **PHP només presenta el xat públic** — layout, widget, context de pàgina; no executa el LLM ni gestiona PDFs.
7. **Panell admin al Python** — el servei agent inclou una **UI interna mínima** (Fase 5) per a operacions (pujar PDFs, veure estat). No cal tocar el CMS PHP de femturisme per a això. Alternativa v1: només CLI si es prefereix sense UI.

---

## 3. Mapa de fases

| Fase | Nom | Depèn de | Lliurable |
|------|-----|----------|-----------|
| **[0](#fase-0)** | [Infraestructura i accessos](#fase-0) | — | MySQL read-only, PostgreSQL agent, staging, `docs/schema.sql` |
| **[1](#fase-1)** | [Servei Python al servidor](#fase-1) | [0](#fase-0) | Agent desplegat, `/api/chat` accessible a xarxa interna |
| **[2](#fase-2)** | [Exploració MySQL i queries](#fase-2) | [0](#fase-0), [1](#fase-1) | `sql-mapeo.md` amb queries per tool |
| **[3](#fase-3)** | [Tools catàleg + MySQL](#fase-3) | [2](#fase-2) | 4 tools operatives via repositoris |
| **[4](#fase-4)** | [Widget a femturisme.cat](#fase-4) | [1](#fase-1), [3](#fase-3) | Globus + panell a la web, proxy mateix domini |
| **[5](#fase-5)** | [Ingesta PDF + vector store](#fase-5) | [0](#fase-0) | Panell admin, pipeline indexació, estat per document |
| **[6](#fase-6)** | [Tool RAG guies](#fase-6) | [5](#fase-5) | `search_municipality_guides` operativa |
| **[7](#fase-7)** | [Xat unificat](#fase-7) | [3](#fase-3), [4](#fase-4), [6](#fase-6) | Un widget; catàleg + guies en producció |
| **[8](#fase-8)** | [Producció i ops](#fase-8) | [7](#fase-7) | Monitorització, límits, runbooks |

**Paral·lelisme recomanat:**

- Les fases **2 i 3** (SQL) poden avançar quan les fases 0–1 estiguin llestes.
- La fase **5** (PDFs) pot anar en paral·lel amb les fases 2–4.
- La fase **4** (widget) requereix la fase 1; convé tenir almenys una tool MySQL a la fase 3 abans de producció.

```
Temps ───────────────────────────────────────────────────────────►

Fase 0 ████
Fase 1    ████
Fase 2      ██████████
Fase 3            ████████
Fase 4                  ██████        (widget; requereix agent + tools)
Fase 5      ████████████              (PDFs; paral·lel)
Fase 6                        ██████
Fase 7                              ████
Fase 8                                  ████
```

---

## 4. Fase 0 — Infraestructura i accessos {#fase-0}

**Objectiu:** permisos, entorns i **dues bases de dades** documentades i accessibles perquè l'equip de l'agent pugui desenvolupar **sense dependre del mantenidor PHP** en el dia a dia.

| # | Tasca | Lliurable concret |
|---|-------|-------------------|
| 0.1 | Usuari MySQL **només lectura** (catàleg femturisme) | Usuari `agent_read@<host>` amb `SELECT` sobre taules de contingut. Sense escriptura. |
| 0.2 | Exportar **schema MySQL** | Fitxer `docs/schema.sql` en **aquest repo** (`agent_femturisme`) |
| 0.3 | Accés al **repo PHP de femturisme** (opcional) | Clone o lectura del codi legacy només si l'schema no n'hi ha prou per entendre JOINs |
| 0.4 | Entorn **staging** | MySQL + **PostgreSQL agent** accessibles; xarxa/firewall cap al host Python |
| 0.5 | Decisió desplegament Python | Docker Compose / systemd / VM — diagrama amb IP, port, qui desplega |
| 0.6 | Variables d'entorn | `.env.example`: `AGENT_*`, `MYSQL_*`, `POSTGRES_*` (o `AGENT_DB_*`), `VECTOR_*` |
| 0.7 | **BD agent PostgreSQL** | Instància staging (i pla producció): host, port, nom BD, backup acordat |
| 0.8 | Usuari BD agent | Usuari `agent_app@…` **read-write** només sobre la BD de l'agent (no MySQL femturisme) |
| 0.9 | Decisió vector store | **pgvector** (mateixa PostgreSQL, recomanat) vs Qdrant + PostgreSQL — documentat abans Fase 5 |

### Què és l'«schema» i per què va al repo de l'agent?

Aquí **schema** = **estructura de la base de dades MySQL de femturisme**, no codi d'aplicació.

És un volcat **només de DDL** (definició de taules, columnes, índexs, FKs), **sense files de dades**:

```bash
mysqldump --no-data -h <host> -u <user> -p femturisme > docs/schema.sql
```

El fitxer resultant conté línies de l'estil `CREATE TABLE experiencies (...)` — serveix per veure quines taules existeixen, com es relacionen i quines columnes hi ha **sense connectar a producció** cada vegada que algú de l'equip obre el projecte.

| Pregunta | Resposta |
|----------|----------|
| De quin repo parlem? | Del repo **nou de l'agent**: `agent_femturisme` (aquest projecte Python). **No** del repo PHP de la web. |
| Per què commitejar-lo aquí? | Perquè qualsevol dev de l'agent tingui l'estructura BD versionada a Git, pugui obrir-la a DBeaver/Workbench offline i revisar PRs de les fases 2–3 sense VPN permanent. |
| Substituïx connectar a MySQL? | **No.** Segueix fent falta l'usuari read-only (0.1) per provar queries amb dades reals a staging. L'schema és la **documentació estructural**; la connexió és la **validació amb dades**. |
| Qui el genera i quan? | Ops o el mantenidor MySQL, **una vegada en tancar la Fase 0** (i de nou quan canviï l'schema a producció). El dev de l'agent el commitea a `docs/schema.sql`. |

### Repo PHP (tasca 0.3) — aclariment

És **opcional** i **distint** de l'schema:

- **Schema** → estructura de taules (SQL estàtic a `docs/schema.sql`).
- **Repo PHP** → codi font de femturisme.cat, útil només si hi ha lògica de negoci enterrada a PHP (filtres de «publicat», JOINs estranys) que no es dedueix del `CREATE TABLE`.

Si l'equip PHP pot documentar regles de negoci per escrit, el clone del repo PHP pot no ser necessari.

### BD pròpia de l'agent (PostgreSQL)

L'agent necessita **una segona base de dades**, independent de la MySQL de femturisme. **No es pot reutilitzar la MySQL read-only** per pujar PDFs, guardar embeddings ni l'estat d'indexació.

```
Servei Python (agent)
    │
    ├── MySQL femturisme (read-only)     → catàleg: ofertes, agenda, allotjaments, rutes
    │
    └── PostgreSQL agent (read-write)    → PDFs: guide_documents, chunks, embeddings (pgvector)
```

| Pregunta | Resposta |
|----------|----------|
| **Cal PostgreSQL?** | Cal una **BD pròpia de l'agent**. El pla recomana **PostgreSQL** (amb extensió **pgvector** si s'acorda a 0.9). |
| **És la mateixa BD que femturisme?** | **No.** MySQL femturisme = dades del web (legacy). PostgreSQL agent = dades **només de l'agent** (guies PDF, vectors, estat). |
| **Què s'hi guarda?** | Taula `guide_documents` (estat de cada PDF), chunks de text, vectors d'embedding (si pgvector), metadades RAG. |
| **On viu?** | Mateix servidor que el Python (Docker Compose `app` + `postgres`), PostgreSQL gestionat (RDS, Supabase…) o VM interna — acordat amb ops a 0.7. |
| **Qui la crea?** | Ops / equip infra en tancar Fase 0; el dev de l'agent configura connexió i migracions (Fase 5). |
| **Staging vs producció** | **Dues instàncies separades** (o dos schemas/BDs): no indexar PDFs de prova a producció. |

**Opcions de vector store (tasca 0.9):**

| Opció | BD agent | On van els vectors | Notes |
|-------|----------|-------------------|-------|
| **A — recomanada v1** | PostgreSQL + pgvector | Mateixa PostgreSQL | Un sol servei; menys peça móbil |
| **B** | PostgreSQL (metadades) | Qdrant (contenidor apart) | Útil si ja teniu Qdrant o PDFs molt grans |
| **C — només dev** | SQLite | Chroma local | No per producció; prototip ràpid |

**Variables d'entorn** (afegir a `.env.example`, tasca 0.6):

```bash
# MySQL femturisme (read-only, catàleg)
MYSQL_HOST=...
MYSQL_USER=agent_read
MYSQL_PASSWORD=...
MYSQL_DATABASE=femturisme

# PostgreSQL agent (read-write, PDFs + vectors)
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_USER=agent_app
POSTGRES_PASSWORD=...
POSTGRES_DATABASE=agent_femturisme
# Si pgvector: mateixa URL; extensió CREATE EXTENSION vector; a la primera migració
```

**Docker Compose mínim (exemple staging, tasca 0.5/0.7):**

```yaml
services:
  agent:
    build: .
    environment:
      MYSQL_HOST: ...
      POSTGRES_HOST: postgres
    depends_on: [postgres]
  postgres:
    image: pgvector/pgvector:pg16
    volumes: [agent_pg_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_USER: agent_app
      POSTGRES_PASSWORD: ...
      POSTGRES_DB: agent_femturisme
```

**Checklist BD agent (ops + dev):**

- [ ] PostgreSQL staging aixecat i accessible des del host Python.
- [ ] Usuari `agent_app` amb permisos només sobre `agent_femturisme` (no superuser).
- [ ] Decisió 0.9 documentada (pgvector vs Qdrant).
- [ ] Backup/restauració acordats (PDFs + vectors costen de regenerar).
- [ ] Connexió provada des de dev (`psql` o script Python) abans de Fase 5.

**Tancament:**

- [ ] Connexió MySQL read-only des de la màquina de desenvolupament de l'agent.
- [ ] `docs/schema.sql` commitejat a `agent_femturisme` (DDL MySQL, sense dades).
- [ ] **PostgreSQL agent** accessible a staging; credencials a `.env.example`.
- [ ] Staging acordat amb ops (host, port, firewall cap a Python).

---

## 5. Fase 1 — Servei Python al servidor {#fase-1}

**Objectiu:** agent Python en execució al servidor amb connectivitat a **MySQL (catàleg)** i **PostgreSQL (agent)**, i endpoint HTTP operatiu.

| # | Tasca | Detall |
|---|-------|--------|
| 1.1 | Empaquetat | Docker Compose o imatge; `requirements.txt` |
| 1.2 | Desplegament staging | Contenidor/procés al servidor accessible des de xarxa interna |
| 1.3 | Configuració | `AGENT_*`, `MYSQL_*`, `POSTGRES_*`, `VECTOR_*` |
| 1.4 | Health check | `GET /health` o equivalent |
| 1.5 | Endpoints API | `POST /api/chat`, `POST /api/session/reset` (SSE) |
| 1.6 | Static files | Servir `app/static/chat/` (widget reutilitzable) i preparar `app/static/admin/` (Fase 5) |
| 1.7 | Prova connexió MySQL | Script que valida pool read-only des del servei |
| 1.8 | Prova connexió PostgreSQL | Script que valida connexió a BD agent (Fase 0) |
| 1.9 | Smoke test agent | Pregunta de prova; resposta SSE |

**Tancament:**

- [ ] Servei accessible a staging (IP/port intern o URL).
- [ ] MySQL accessible des del contenidor/procés.
- [ ] PostgreSQL agent accessible des del contenidor/procés.
- [ ] `/api/chat` respon.

---

## 6. Fase 2 — Exploració MySQL i disseny de queries {#fase-2}

**Guia detallada per al developer:** [fase-2-tools-mysql-ca.md](./fase-2-tools-mysql-ca.md) (preguntes freqüents, passos, exemples).  
**Plantilla lliurable:** [sql-mapeo.md](./sql-mapeo.md).

**Objectiu:** entendre l'schema legacy i dissenyar, **per a cada tool de catàleg**, la SQL parametritzada que el backend executarà quan el LLM invoque aquesta tool.

### Per què queries predefinides i no SQL generat al vol pel LLM?

És un dubte habitual entre programadors: *«Si li dic a Claude què vull, per què no escriu el `SELECT` i l'executa? No ens estalviaríem molta complexitat?»*

**Resposta curta:** sí és **tècnicament possible**; és una **decisió d'arquitectura**, no una limitació del LLM. El LLM **sí decideix què buscar** (tool + paràmetres); el backend **no li deixa escriure SQL lliure** contra MySQL en producció.

**Flux adoptat:**

```
Usuari: "Experiències familiars al Berguedà aquest cap de setmana"
    │
    ▼
LLM tria tool + arguments (visibles al SCHEMA):
    search_experiences(destination="Berguedà", category="Familiar")
    │
    ▼
Backend Python (execute()):
    • Valida paràmetres
    • Executa SQL fixa + placeholders (:destination, :category)
    • LIMIT 20, només taules permeses
    • Normalitza files → JSON Annex B
    │
    ▼
LLM redacta resposta a l'usuari amb les cards rebudes
```

El LLM **no veu** el SQL ni l'schema MySQL. Només ve el **SCHEMA de la tool** (nom, descripció, paràmetres permesos) i el **JSON de resultats**.

**Arguments resumits** (taula comparativa, riscos de read-only, alternatives híbrides i decisió formal): **[Annex D — Tools parametritzades vs text-to-SQL](#anexo-d)**.

**Què documenta `sql-mapeo.md`:** especificació per a programadors (taules, SQL parametritzada, mapatge JSON, regles de negoci, casos de prova). La SQL viu a `app/db/repositories/*.py`; el LLM no la llegeix. Vegeu també [Annex D](#anexo-d).

### Tools de catàleg

| Tool | Domini |
|------|--------|
| `search_experiences` | Ofertes, activitats, experiències |
| `search_accommodations` | Allotjaments |
| `search_events` | Agenda, esdeveniments |
| `search_routes` | Rutes |

### Metodologia per tool

**A. Explorar schema**

- Taules de contingut, relacions, ubicació, categories, dates, imatges, slugs.
- Diagrama ER parcial a `sql-mapeo.md`.

**B. Definir necessitats del LLM**

- Paràmetres SCHEMA: destination, category/type, date_from/date_to.
- Camps JSON de sortida (Annex B) + extres: preu, coordenades, dates exactes…
- Regles: publicat, vigent, ordre, LIMIT.

**C. Escriure query parametritzada**

- JOINs, WHERE, ORDER BY, LIMIT.
- Sense concatenació de strings; placeholders.

**D. Validar a MySQL**

- 3–5 casos reals (Berguedà + Familiar, Girona + hotel, agenda cap de setmana…).
- URLs canòniques construïbles des de slug/id.

**E. Documentar a sql-mapeo.md**

### Lliurable: `docs/sql-mapeo.md`

Per a cada tool:

1. Taules i relacions.
2. Query SQL final.
3. Mapatge columna → camp JSON.
4. Regles de negoci.
5. Casos de prova (paràmetres + resultat esperat).

### Eines

- DBeaver / MySQL Workbench + `schema.sql`
- Repo PHP (només si aclareix JOINs no obvis)
- General log MySQL a staging (últim recurs)

**Tancament:**

- [ ] 4 tools amb query documentada i provada a MySQL.
- [ ] SCHEMA de tools revisat si cal ampliar paràmetres o descripcions.

---

## 7. Fase 3 — Tools de catàleg amb MySQL {#fase-3}

**Guia detallada per al developer:** [fase-3-tools-mysql-ca.md](./fase-3-tools-mysql-ca.md) (passos, fitxers, exemples de codi, com provar).

**Objectiu:** implementar capa de dades; cada `execute()` delega en un repositori SQL.

| # | Tasca | Detall |
|---|-------|--------|
| 3.1 | `app/db/connection.py` | Pool, timeout, read-only |
| 3.2 | Repositoris | `ExperiencesRepository`, `AccommodationsRepository`, `EventsRepository`, `RoutesRepository` |
| 3.3 | Implementar queries | Segons `sql-mapeo.md` |
| 3.4 | Normalitzador | `row → dict` segons Annex B |
| 3.5 | Refactor `execute()` | Cada tool crida el seu repo |
| 3.6 | Tests | Casos de `sql-mapeo.md` automatitzats a `tests/sql/` |
| 3.7 | Integració agent | Xat de prova via `/api/chat` amb LLM real |

**Tancament:**

- [ ] Les 4 tools retornen JSON des de MySQL a staging.
- [ ] Tests SQL passen.
- [ ] Respostes de l'agent coherents en proves manuals.

---

## 8. Fase 4 — Widget a femturisme.cat {#fase-4}

**Objectiu:** globus flotant a totes les pàgines; panell de xat overlay; mateix domini.

| # | Tasca | Detall |
|---|-------|--------|
| 4.1 | Widget JS/CSS | Globus fix bottom-right; panell obrir/tancar; reutilitzar lògica SSE existent |
| 4.2 | Include PHP | Footer/layout global |
| 4.3 | Reverse proxy | `/api/chat`, `/api/session/reset` → servei Python |
| 4.4 | Estil | Alineat amb femturisme.cat |
| 4.5 | `page_context` | Enviar `{ section, ubicacio, municipality }` des de PHP/URL |
| 4.6 | Proves | Desktop, mòbil, SSE estable |
| 4.7 | Producció | Rollout progressiu si cal |

**Tancament:**

- [ ] Globus visible; clic obre el xat.
- [ ] Conversa funcional contra agent amb MySQL.
- [ ] Sense errors CORS (same-origin).

---

## 9. Fase 5 — Ingesta de PDFs i vector store {#fase-5}

**Objectiu:** permetre a l'equip femturisme **pujar PDFs de guies municipals**, processar-los automàticament (extracció → chunks → embeddings) i **saber en tot moment** quins documents hi ha, en quin estat estan i si la indexació ha anat bé.

### On es puja i qui ho fa

Els PDFs **no es pugen des de femturisme.cat** ni des del widget de xat. El xat només **consulta** guies ja indexades.

| Pregunta | Resposta v1 |
|----------|-------------|
| **Des d'on es puja?** | **Panell d'administració** al servei Python de l'agent: `https://<host-agent>/admin/guides` (xarxa interna, VPN o accés restringit per IP + login). |
| **Qui el fa servir?** | Personal femturisme / equip tècnic autoritzat (no usuaris finals del web). |
| **Alternativa per a devs** | CLI: `python scripts/ingest_pdf.py --file … --municipality …` (mateix pipeline que la UI). |
| **On es guarda el PDF original?** | Disc del servidor agent: `data/guides/{doc_id}/original.pdf` (o bucket S3-compatible si s'acorda amb ops). |
| **On es guarda l'estat?** | **BD pròpia de l'agent** (PostgreSQL recomanat si s'usa pgvector; no la MySQL read-only de femturisme). |

### Frontend admin al servei Python (aclarament)

Sí: el servei Python tindrà un **frontend petit i intern**, separat del web públic. Això **no surtia explícit** al diagrama inicial; es concreta aquí.

| Pregunta | Resposta |
|----------|----------|
| **Python tindrà frontend?** | **Sí, però només d'administració interna** (pujar PDFs, llistar documents, veure status, reindexar). No és una segona web pública. |
| **Què NO inclou aquest frontend?** | No substitueix femturisme.cat. No edita contingut MySQL, no gestiona usuaris del CMS PHP, no és el xat del visitant. |
| **Com es implementa v1?** | Flask serveix HTML + JS/CSS des de `app/static/admin/` (pàgines senzilles: llista, formulari pujada, detall document). Sense React ni framework pesat. |
| **Qui hi accedeix?** | URL del host agent (`https://agent-intern.femturisme…/admin/guides`), protegida per login basic / token / VPN — **no indexada ni enllaçada** des del web públic. |
| **Per què al Python i no al PHP?** | El pipeline ingest (extracció, embedding, vector store) viu al Python; col·locar l'admin aquí evita duplicar lògica i APIs al CMS legacy. |
| **Alternativa sense UI?** | **CLI** (`scripts/ingest_pdf.py`) per a v1 tècnic; el panell web es pot ajornar si l'equip prefereix operar per terminal. |
| **Alternativa futura** | Panell dins el backoffice PHP de femturisme que crida l'API admin del Python — possible post-v1, però **no és el pla v1**. |

**Components del frontend admin (v1):**

| Pantalla | Ruta | Funció |
|----------|------|--------|
| Llista de guies | `GET /admin/guides` | Taula amb tots els PDFs i status |
| Pujar guia | `GET /admin/guides/upload` | Formulari: fitxer + municipi + títol |
| Detall document | `GET /admin/guides/{doc_id}` | Comptadors, error, botons Reindexar / Provar cerca |

El **widget de xat** que veu el visitant continua sent JS servit des del Python (o copiat al PHP a la Fase 4) i incrustat a femturisme.cat — és un altre frontend amb un altre propòsit.

```
┌─────────────────────────────────────────────────────────────────────┐
│ Equip femturisme (navegador intern / VPN)                           │
│  Panell /admin/guides  →  pujar PDF + municipi + títol              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ POST /admin/api/guides/upload
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Servei agent Python                                                 │
│  1. Desa PDF a data/guides/{doc_id}/                                │
│  2. Registra document a guide_documents (status: pending)           │
│  3. Pipeline ingest (extracció → chunks → embeddings → vector store)│
│  4. Actualitza status → indexed | failed                          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ BD agent (guide_documents) │   │ Vector store              │
│ estat, comptadors, errors  │   │ chunks + embeddings       │
└───────────────────────────┘   └───────────────────────────┘
```

### Flux d'ingesta (pas a pas)

| Pas | Què passa | On es veu |
|-----|-----------|-----------|
| **1. Pujada** | L'operador selecciona fitxer PDF, municipi i títol; el backend genera `doc_id` (UUID). | Panell admin: fila nova amb status `pending`. |
| **2. Extracció** | `pymupdf` / `pdfplumber` llegeix text per pàgina; es compta `pages_count`. | Status → `extracting`. |
| **3. Chunking** | Es divideix en fragments de 500–1000 tokens amb overlap 10–15%; es crea `chunks_count`. | Status → `chunking`. |
| **4. Embeddings** | Cada chunk es passa al model d'embedding (batch); es desa vector + metadades al vector store. | Status → `embedding`; comptador `embedded_chunks_count` puja. |
| **5. Indexació completa** | Quan `embedded_chunks_count == chunks_count`, status → `indexed` i `indexed_at` = ara. | Panell admin: badge verd **Indexat**. |
| **6. Error** | Qualsevol pas pot fallar (PDF buit, API embedding, vector store). | Status → `failed` + `error_message` visible al panell. |

**Reemplaçar un PDF:** es puja una nova versió amb el mateix municipi/títol (o es fa «Reindexar» al panell). El pipeline **esborra els chunks antics** d'aquest `doc_id` al vector store i indexa de nou (`version` incrementa).

### Com sabem quins PDFs estan pujats

Tres llocs complementaris:

| On mirar | Què mostra |
|----------|------------|
| **Panell `/admin/guides`** | Llista de tots els documents: títol, municipi, nom fitxer, data pujada, **status**, pàgines, chunks, model embedding. |
| **API `GET /admin/api/guides`** | Mateix llistat en JSON (per scripts o monitorització). |
| **CLI `python scripts/ingest_pdf.py --list`** | Llistat ràpid des de terminal (dev/staging). |

**Taula de registre** `guide_documents` (BD agent):

| Camp | Exemple | Ús |
|------|---------|-----|
| `doc_id` | `a1b2-…` | Identificador únic |
| `title` | `Guia turística Berga 2024` | Nom visible al panell |
| `municipality` | `Berga` | Filtre RAG per municipi |
| `source_filename` | `guia_berga.pdf` | Nom original del fitxer |
| `storage_path` | `data/guides/a1b2…/original.pdf` | On està el PDF |
| `status` | `indexed` | Estat del pipeline (vegeu taula següent) |
| `error_message` | `Embedding API timeout` | Si `failed`, motiu |
| `pages_count` | `48` | Pàgines extretes |
| `chunks_count` | `120` | Fragments generats |
| `embedded_chunks_count` | `120` | Vectors creats (ha de coincidir) |
| `embedding_model` | `text-embedding-3-small` | Model usat |
| `indexed_at` | `2026-06-23T10:00:00Z` | Quan va acabar OK |
| `version` | `2` | Reindexacions |

**Valors de `status`:**

| Status | Significat |
|--------|------------|
| `pending` | Pujat; pipeline encara no ha començat |
| `extracting` | Llegint text del PDF |
| `chunking` | Dividint en fragments |
| `embedding` | Generant vectors (pot trigar minuts en PDFs grans) |
| `indexed` | **Tot correcte** — disponible per al xat RAG |
| `failed` | Error; cal revisar `error_message` i reintentar |

### Com es fan els embeddings

1. **Model** — acordat a la Fase 5 (p. ex. OpenAI `text-embedding-3-small` o model local). Es guarda a `embedding_model` per traçabilitat.
2. **Quan** — automàticament després de la pujada (job en background a v1; opcional cua Redis/Celery si hi ha molts PDFs).
3. **Com** — per cada chunk de text:
   - Es crida l'API d'embedding (batch de 50–100 chunks per reduir cost).
   - Es fa **upsert** al vector store amb metadades (vegeu JSON més avall).
4. **On viuen** — al **vector store** (pgvector / Qdrant / Chroma), **no** a MySQL femturisme.
5. **Enllaç document ↔ vectors** — tots els chunks d'un PDF comparteixen `doc_id`; la cerca RAG filtra per `municipality` + similaritat vectorial.

**Metadades mínimes per chunk** (al vector store):

```json
{
  "doc_id": "uuid",
  "doc_title": "Guia turística Berga 2024",
  "municipality": "Berga",
  "page": 12,
  "chunk_index": 3,
  "category": "restaurants",
  "source_file": "guia_berga.pdf",
  "embedding_model": "text-embedding-3-small",
  "indexed_at": "2026-06-23T10:00:00Z"
}
```

### Com sabem si ha anat bé

**Criteris automàtics** (el panell i la BD ho reflecteixen):

| Comprovació | Condició d'èxit |
|-------------|-----------------|
| Pipeline completat | `status == indexed` |
| Tots els chunks embeddats | `embedded_chunks_count == chunks_count` i `chunks_count > 0` |
| PDF no buit | `pages_count > 0` |
| Sense error | `error_message IS NULL` |
| Data indexació | `indexed_at` informat |

**Proves manuals** (després de cada pujada o abans de producció):

| Prova | Com fer-la |
|-------|------------|
| **Smoke test al panell** | Botó «Provar cerca» al document: query fixa (p. ex. «restaurants plaça major») → ha de retornar chunks d'aquest `doc_id`. |
| **CLI verify** | `python scripts/ingest_pdf.py --verify {doc_id} --query "restaurants Berga"` |
| **Prova via xat** | Pregunta al widget: «On dinar a Berga segons la guia?» → la resposta ha de citar `doc_title` i pàgina (Fase 6). |
| **Logs** | Log estructurat per ingest: `doc_id`, pas, durada, chunks OK/KO. Alerta si `failed`. |

**Si falla:** al panell es mostra `error_message`; l'operador pot clicar **Reindexar** (`POST /admin/api/guides/{doc_id}/reindex`) sense tornar a pujar el fitxer.

### Tasques d'implementació

| # | Tasca | Detall |
|---|-------|--------|
| 5.1 | Triar vector store + BD agent | pgvector (PostgreSQL) recomanat: metadades + vectors al mateix lloc; alternativa Qdrant + PostgreSQL |
| 5.2 | Panell admin `/admin/guides` | UI mínima Flask (HTML + JS a `app/static/admin/`): llista, pujada, detall, reindexar, provar cerca |
| 5.3 | API admin | `POST /upload`, `GET /guides`, `GET /guides/{id}`, `POST /guides/{id}/reindex`, `POST /guides/{id}/smoke-test` |
| 5.4 | Taula `guide_documents` | Schema anterior; migració a l'arrencar el servei |
| 5.5 | Pipeline `app/rag/ingest.py` | Extracció → chunking → embedding → upsert; actualitza status a cada pas |
| 5.6 | CLI `scripts/ingest_pdf.py` | `--file`, `--list`, `--verify` per devs sense UI |
| 5.7 | Validació | ≥3 PDFs amb `status=indexed`; smoke tests documentats |

**Tancament:**

- [ ] Panell admin accessible a staging (equip femturisme pot pujar un PDF de prova).
- [ ] Es veu la llista de documents amb status i comptadors (`pages`, `chunks`, `embedded`).
- [ ] ≥3 PDFs amb `status=indexed` i smoke test OK per cadascun.
- [ ] Runbook: què fer si `failed` (revisar log, reindexar, contactar dev).

---

## 10. Fase 6 — Tool RAG (guies municipals) {#fase-6}

**Objectiu:** tool per a converses basades en PDFs pujats.

| # | Tasca | Detall |
|---|-------|--------|
| 6.1 | SCHEMA | `search_municipality_guides(query, municipality, category?)` |
| 6.2 | `execute()` | embed query → cerca vectorial filtrada per `municipality` → top-K (només chunks de documents amb `status=indexed`) |
| 6.3 | Resposta JSON | `{ query, municipality, total, results: [{ source, page, summary }] }` |
| 6.4 | Registrar a `ALL_TOOLS` | |
| 6.5 | Avaluació | ~20 preguntes: plaça major, aparcar, història, transport… |

**Exemples d'ús:**

- "Soc a la plaça Major de Berga, recomana'm restaurants a prop"
- "On puc aparcar al centre segons la guia?"
- "Explica'm la Patum segons el fulletó del municipi"

**Limitació v1:** sense GPS; precisió segons text del PDF i lloc que nombri l'usuari.

**Tancament:**

- [ ] Tool operativa a staging amb PDFs reals.
- [ ] Respostes citen document i pàgina.

---

## 11. Fase 7 — Xat unificat {#fase-7}

**Objectiu:** un globus, un panell, catàleg MySQL + guies PDF sense que l'usuari triï mode.

| # | Tasca | Detall |
|---|-------|--------|
| 7.1 | `ALL_TOOLS` | 4 catàleg + guies RAG |
| 7.2 | System prompt | Quan catàleg, quan guies, quan ambdós; idioma usuari |
| 7.3 | `page_context` | Hint de municipi/secció des de la pàgina actual |
| 7.4 | Multi-tool | Permetre catàleg + guies en un mateix torn |
| 7.5 | Suggeriments UI | Contextuals segons secció de la web |
| 7.6 | Proves | ~30 converses (catàleg, guies, mixtes) |

**Routing v1 (recomanat):** LLM tria tools via schemas; sense router extern.

**Exemple mixt:**

> "Som a Berga, què puc fer avui i on dinar segons la guia?"

Tools: `search_events` + `search_municipality_guides`.

**Tancament:**

- [ ] Un endpoint, un widget.
- [ ] Routing correcte en ≥80% casos de prova acordats.

---

## 12. Fase 8 — Producció i operacions {#fase-8}

| # | Tasca |
|---|-------|
| 8.1 | Rate limiting a `/api/chat` |
| 8.2 | Logs: tool_calls, latència SQL, latència vector, LLM |
| 8.3 | Alertes: BD, vector store, API keys, error rate |
| 8.4 | Historial de sessió persistent (Redis/DB) si multi-instància |
| 8.5 | Streaming LLM natiu (opcional) |
| 8.6 | Runbooks | BD caiguda, query lenta, ingest PDF `failed`, índex vector desactualitzat |
| 8.7 | Documentació operativa per a l'equip femturisme |

---

## 13. Criteris d'èxit

| Àrea | Criteri |
|------|---------|
| **Integració web** | Globus a femturisme.cat; xat same-origin |
| **Catàleg** | 4 tools MySQL; dades útils per al LLM |
| **Guies** | PDFs indexats; respostes amb font |
| **Xat únic** | L'usuari no distingeix orígens de dades |
| **Ops** | Desplegament reproduïble; credencials segregades |

---

## 14. Riscos i decisions pendents

| Risc | Mitigació |
|------|-----------|
| Schema MySQL legacy opac | Exploració Fase 2; suport mantenedor PHP; general log |
| Queries lentes | EXPLAIN; índexs; LIMIT; cache futur |
| PDFs sense detall geogràfic | Metadades manuals; comunicar límit v1 |
| Cost LLM + embeddings | Models lleugers; límits per sessió |
| Desfasament dades web vs agent | Mateixa BD; regles de negoci explícites al SQL |

**Decisions pendents:**

- [x] Catàleg MySQL: tools parametritzades vs text-to-SQL → **tools parametritzades a v1** ([Annex D](#anexo-d))
- [ ] Vector store: pgvector (mateixa PostgreSQL) vs Qdrant + PostgreSQL → decidir a **Fase 0** (tasca 0.9)
- [ ] Hosting Python: mateixa màquina que PHP vs dedicat
- [ ] Flask vs migració FastAPI
- [ ] Persistència historial xat a v1
- [ ] Model embedding i LLM producció

---

## 15. Annex A — Checklist SQL per tool

Completar a la **Fase 2** abans d'implementar a la **Fase 3**.

| # | Checklist |
|---|-----------|
| C1 | Taules i JOINs identificats |
| C2 | Filtre `destination` mapat |
| C3 | Filtres opcionals (tipus, categoria, dates) mapats |
| C4 | Regles de negoci (publicat, vigent, ordre) |
| C5 | Camps JSON definits (Annex B + extres) |
| C6 | Query a `sql-mapeo.md` |
| C7 | 3–5 casos provats a MySQL |
| C8 | URLs de resultats correctes |

**Paràmetres per tool (v1.1 — veure [dominio-femturisme-ca.md](dominio-femturisme-ca.md)):**

| Tool | Paràmetres SCHEMA |
|------|-------------------|
| `search_establishments` | `destination`, `type?` |
| `search_articles` | `destination?`, `topic?`, `query?` |
| `search_destinations` | `destination`, `region?` |
| `search_routes` | `destination`, `type?` |
| `search_events` | `destination`, `date_from?`, `date_to?` |
| `search_experiences` | `destination`, `category?`, `establishment?` |

**Deprecat:** `search_accommodations` → `search_establishments`. Significat de `search_experiences` redefinit (experiències promocionals, no «ofertes» genèric).

---

## 16. Annex B — Contracte JSON cap al LLM

### Card de catàleg

```json
{
  "id": "string | null",
  "type": "string | null",
  "title": "string",
  "location": "string | null",
  "description": "string | null",
  "url": "string | null",
  "image": "string | null",
  "date": "string | null"
}
```

### Wrapper (ex. experiences)

```json
{
  "destination": "string",
  "category": "string | null",
  "total": "number | null",
  "results": [],
  "error": "string | null"
}
```

### Resultat RAG (guies)

```json
{
  "query": "string",
  "municipality": "string",
  "total": "number",
  "results": [
    {
      "source": "string",
      "page": "number | null",
      "summary": "string",
      "doc_id": "string | null"
    }
  ]
}
```

---

## 17. Annex C — Estructura de carpetes

```
agent_femturisme/
├── app/
│   ├── admin/
│   │   └── guides_routes.py    ← panell /admin/guides (Fase 5)
│   ├── db/
│   │   ├── connection.py
│   │   └── repositories/
│   ├── rag/
│   │   ├── ingest.py           ← pipeline PDF → chunks → embeddings
│   │   ├── embedder.py
│   │   ├── vector_store.py
│   │   └── municipality_guides.py
│   ├── services/
│   └── static/
│       ├── chat/
│       └── admin/              ← UI llistat i pujada PDFs
├── data/
│   └── guides/                 ← PDFs originals per doc_id
├── docs/
│   ├── agente.md
│   ├── plan-integracion.md
│   └── sql-mapeo.md
├── scripts/
│   └── ingest_pdf.py
└── tests/
```

---

## 18. Annex D — Tools parametritzades vs text-to-SQL {#anexo-d}

Document de decisió arquitectònica per a l'equip de desenvolupament. Respon: *per què el backend no deixa el LLM escriure SQL lliure contra MySQL? No simplificaria l'agent?*

### D.1 La pregunta

En un xat amb tool use, el LLM pot rebre una tool genèrica:

```json
{
  "name": "execute_sql",
  "parameters": {
    "query": "SELECT titol, slug FROM experiencies WHERE ..."
  }
}
```

El backend executaria aquesta cadena contra MySQL i retornaria les files al LLM. **Això és possible.** Molts prototips i demos d'«agent + base de dades» funcionen exactament així.

La pregunta rellevant no és «es pot?» sinó «quina complexitat eliminem i quina complexitat movem a un altre lloc?».

### D.2 Dues arquitectures comparades

#### A) Tools parametritzades (decisió d'aquest pla)

```
Usuari (NL) → LLM tria tool + params → Python executa SQL fixa → JSON normalitzat → LLM respon
```

- El LLM ve: **SCHEMA de 4–5 tools** (nom, descripció, paràmetres).
- El LLM **no ve**: schema MySQL, noms de taules, SQL.
- El backend controla: taules, JOINs, regles de negoci, `LIMIT`, format de sortida.

#### B) Text-to-SQL al vol (alternativa descartada per a v1)

```
Usuari (NL) → LLM genera SELECT → Python executa tal qual → files crues → LLM respon
```

- El LLM ve: **schema complet** (o un resum) + instruccions de generar SQL.
- El LLM **escriu**: la query en cada torn.
- El backend ha de: validar, restringir, limitar, normalitzar — o confiar cegament.

### D.3 Què sembla estalviar text-to-SQL

| El que no caldria (en principi) | Detall |
|---------------------------------|--------|
| 4 repositoris Python | Una sola tool `execute_sql` |
| `sql-mapeo.md` per tool | El LLM «descobreix» taules al vol |
| Ampliar paràmetres SCHEMA | Qualsevol filtre seria SQL ad hoc |
| Fase 2–3 llarga | MVP més ràpid per provar connexió BD |

Per a un **experiment intern** o una **demo**, això pot ser cert.

### D.4 Quina complexitat no desapareix (només canvia de lloc)

Muntar text-to-SQL en **producció** davant usuaris reals exigeix capes que, amb tools parametritzades, ja estan resoltes en codi:

| Capa | Tools parametritzades | Text-to-SQL en producció |
|------|----------------------|---------------------------|
| Conèixer l'schema | L'estudia el dev a la Fase 2 | Cal **injectar l'schema al LLM** en cada torn (milers de tokens) o resumir-lo malament |
| Regles de negoci (`publicat = 1`, dates vigents, idioma…) | Van a la SQL fixa del repo | El LLM ha d'**inferir-les** o les omet |
| Límit de files | `LIMIT 20` en codi | Validador que **rebutgi o reescrigui** queries sense `LIMIT` |
| Taules permeses | Només les del repositori | Parser + allowlist: **només `SELECT`**, només taules X/Y/Z |
| Format al xat | JSON estable ([Annex B](#16-annex-b--contracte-json-cap-al-llm)) | Normalitzador post-query: files → cards amb `title`, `url`, `image` |
| Tests automatitzats | Casos fixos a CI (`destination=Berguedà` → N files) | La SQL **canvia cada torn** i amb cada versió del model |
| Depuració | «La query d'experiences filtra malament el JOIN X» | «Claude va generar una altra SQL ahir que funcionava» |
| Cost/latència LLM | Prompt petit (només SCHEMA de tools) | Schema gran + SQL generada + reintents si falla |

**Conclusió:** no elimines la Fase 2; la converteixes en «posar tot l'schema legacy al prompt i confiar que el model l'interpreti bé en cada pregunta».

### D.5 Per què MySQL read-only no resol el problema

L'usuari `agent_read` sense permisos d'escriptura **evita esborrar o modificar dades**, però **no limita què es pot llegir** ni **quant costa llegir-ho**.

Exemples de queries que un LLM pot generar sense mala intenció:

```sql
-- Taules sensibles (si existeixen i l'usuari té SELECT)
SELECT email, password_hash FROM users LIMIT 1000;

-- Cartesian product / query costosa
SELECT * FROM orders o
JOIN order_items i ON ...
JOIN products p ON ...
JOIN categories c ON ...;

-- Columnes inventades (error en runtime)
SELECT titol, allows_dogs FROM experiencies WHERE zona = 'Berguedà';
-- → Unknown column 'allows_dogs'
```

Els errors habituals no són atacs; són **al·lucinacions de columnes**, **JOINs incorrectes** i **oblidar filtres de negoci** en schemas legacy amb noms críptics (`tbl_cnt`, `rel_ubicacio_2`, etc.).

### D.6 El problema concret de femturisme

Hi ha tres capes que l'agent ha d'encertar alhora:

| Capa | Contingut | Amb text-to-SQL |
|------|-----------|-----------------|
| **1. Schema legacy** | Taules, relacions, noms no obvis | El LLM ha d'encertar JOINs en cada torn |
| **2. Regles de negoci** | Publicat, vigent, idioma — sovint a PHP, no a FK | El LLM no les coneix llevat que estiguin documentades al prompt |
| **3. Contracte de producte** | Cards amb URL canònica, imatge, títol ([Annex B](#16-annex-b--contracte-json-cap-al-llm)) | Les files SQL crues no coincideixen amb el que el xat ha de mostrar |

Amb **tools parametritzades**, el LLM només resol la capa d'**intenció** («què buscar»). Les capes 1–3 les garanteix el backend en codi revisat.

### D.7 Quina flexibilitat sí aporta el LLM (sense SQL lliure)

El LLM ja aporta la flexibilitat que l'usuari percep:

| Capacitat | Exemple |
|-----------|---------|
| Triar tool(s) | Agenda + guia PDF en la mateixa pregunta |
| Inferir paràmetres | «Berguedà en família» → `destination`, `category` |
| Criteris tous | «Amb gossos» → filtra sobre `description` del JSON |
| Combinar resultats | Barreja catàleg MySQL + chunks RAG a la resposta |
| Idioma i to | Respon en català/castellà segons l'usuari |

Aquesta flexibilitat **no requereix** que el LLM escrigui SQL.

### D.8 Comparació d'esforç total (v1, 4 dominis de catàleg)

| Dimensió | Tools parametritzades | Text-to-SQL al vol |
|----------|----------------------|---------------------|
| Complexitat upfront | Alta (Fase 2–3, una vegada) | Baixa (tool genèrica ràpida) |
| Complexitat ongoing | Baixa (canvis en PR) | Alta (validadors, prompt schema, debugging) |
| Risc en producció | Baix | Mitjà–alt |
| Predictibilitat | Alta | Baixa |
| Testabilitat a CI | Alta | Baixa |
| Superfície de dades exposada | Mínima (taules de catàleg) | Tota taula amb `SELECT` permès |

Per a **quatre dominis acotats** (ofertes, allotjaments, agenda, rutes), parametritzar sol implicar **menys treball total** que muntar un sandbox SQL robust.

### D.9 Què caldria implementar igual amb text-to-SQL

Si es triés text-to-SQL per a producció, el backend necessitaria com a mínim:

1. **Injecció de schema** — `docs/schema.sql` o subconjunt en cada request (cost tokens).
2. **Parser SQL** — rebutjar `INSERT`, `UPDATE`, `DELETE`, `DROP`, subqueries perilloses, múltiples statements.
3. **Allowlist de taules** — només taules de catàleg; rebutjar la resta.
4. **`LIMIT` obligatori** — injectar o rebutjar si falta (p. ex. màx. 50 files).
5. **Timeout de query** — p. ex. 2 s; matar queries lentes.
6. **Normalitzador de sortida** — files → JSON Annex B (URLs, imatges, slugs).
7. **Logging de queries generades** — per auditar què va executar el LLM.
8. **Reintents** — quan la SQL falla per columna inexistent (comú).

Això és comparable en esforç a implementar 4 repositoris, però **més fràgil** en runtime.

### D.10 Alternatives intermèdies

| Alternativa | Descripció | Quan té sentit |
|-------------|------------|----------------|
| **Vistes SQL a MySQL** | `CREATE VIEW v_experiences_public AS …`; el LLM només consulta vistes | Redueix taules sensibles; no elimina al·lucinacions ni JSON inestable |
| **Text-to-SQL només a staging** | Tool interna per a devs que exploren l'schema | Fase 2 d'exploració; sense tràfic d'usuaris |
| **Híbrid post-v1** | Tools parametritzades + cinena tool molt restringida per a casos rars | Només si apareix demanda real no coberta per les 4 tools |
| **Schema-on-read al prompt** | Resum manual de 20 taules clau al system prompt | Compromís fràgil; requereix manteniment manual |

### D.11 Decisió formal (v1)

| Aspecte | Decisió |
|---------|---------|
| **Mecanisme catàleg** | Tools parametritzades: `search_experiences`, `search_accommodations`, `search_events`, `search_routes` |
| **SQL** | Fixa a `app/db/repositories/*.py`; documentada a `sql-mapeo.md` |
| **Visibilitat LLM** | SCHEMA de tools + JSON de resultats; **sense** schema MySQL ni SQL |
| **Text-to-SQL** | **No** al xat de producció v1 |
| **Revisió** | Després de v1 en producció, si >20% de preguntes de catàleg no es resolen amb les 4 tools, avaluar ampliar paràmetres o vistes SQL abans que text-to-SQL |

### D.12 Resposta llista per compartir amb el client

> «Per què no deixem que Claude escrigui la query?»
>
> Perquè **sí es pot**, però **no redueix la complexitat total** en un entorn de producció amb schema legacy: desplaça el treball d'«escriure quatre queries ben fetes» a «validar SQL arbitrària, injectar schema, normalitzar resultats i depurar queries trencades en cada conversa». Per a un catàleg turístic amb respostes en cards i dades sensibles a la mateixa BD, les tools parametritzades ofereixen **menys sorpreses**, **tests reproduïbles** i **menor superfície d'exposició de dades**. El LLM segueix sent flexible en *què* buscar i *com* respondre; el que fixem en codi és *com* accedir a MySQL de forma segura i estable.

---

## Proper pas

1. **[Fase 0](#fase-0)** — credencials MySQL read-only + PostgreSQL agent a staging + commitejar `docs/schema.sql`.
2. **[Fase 1](#fase-1)** — desplegar servei Python a staging amb connexió MySQL.
3. **[Fase 2](#fase-2)** — primera query documentada a `sql-mapeo.md` per a `search_experiences`.
