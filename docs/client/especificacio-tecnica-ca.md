# Especificació tècnica — Assistent de xat femturisme.cat (v1.1)

Document d'**implementació i integració** per a desenvolupadors i operacions.


| Camp                   | Valor                                                                    |
| ---------------------- | ------------------------------------------------------------------------ |
| **Versió**             | 1.1                                                                      |
| **Data**               | 2026-06-28                                                               |
| **Domini**             | [dominio-femturisme-ca.md](dominio-femturisme-ca.md)                     |
| **Document funcional** | [especificacio-funcional-ca.md](especificacio-funcional-ca.md)           |
| **Referència interna** | [plan-integracion-ca.md](plan-integracion-ca.md), [agente.md](agente.md) |


---

## 1. Arquitectura lògica

Arquitectura lògica

**Flux d'un missatge de xat:**

1. El navegador envia `POST /api/chat` al domini femturisme.cat (proxy cap al Python).
2. El servei agent interpreta la pregunta (model de llenguatge) i decideix quines consultes executar.
3. Les consultes de catàleg llegeixen **MySQL** (SQL parametritzada). Les consultes de guia llegeixen **PostgreSQL + vectors**.
4. El servei agent genera la resposta final i l'emet per **SSE** al client.
5. El widget JS renderitza text (Markdown) i enllaços.

Diagrama visual: [assets/diagrama-arquitectura.png](assets/diagrama-arquitectura.png).

---

## 2. Repartiment de responsabilitats

### 2.1 Resum per equip


| Component                 | Responsable típic           | Tasques                                                                         |
| ------------------------- | --------------------------- | ------------------------------------------------------------------------------- |
| **femturisme.cat (PHP)**  | Consultora / mantenedor web | Globus, panell xat, include layout, proxy `/api/chat`, `page_context`, estils   |
| **Servei agent (Python)** | Equip agent o consultora    | API xat, consultes catàleg, pipeline PDF, panell admin, connexions BD           |
| **Operacions**            | Consultora                  | Usuari MySQL read-only, PostgreSQL gestionat, Docker, `.env`, firewall, backups |


### 2.2 Tasques PHP (referència RF)


| #        | Tasca                                                                    | RF / CA          |
| -------- | ------------------------------------------------------------------------ | ---------------- |
| T-PHP-01 | Incrustar globus + panell JS/CSS al layout global                        | RF-0101–0103     |
| T-PHP-02 | Configurar reverse proxy `/api/chat`, `/api/session/reset` → host Python | RF-0109, RNF-002 |
| T-PHP-03 | Enviar `page_context` opcional al body de `/api/chat`                    | RF-0501          |
| T-PHP-04 | Botó «Nova conversa» cridant `/api/session/reset`                        | RF-0107, CA-0105 |
| T-PHP-05 | Proves desktop/mòbil staging                                             | RNF-008          |


### 2.3 Tasques Python


| #       | Tasca                                                            | RF / CA          |
| ------- | ---------------------------------------------------------------- | ---------------- |
| T-PY-01 | Desplegar Flask amb `/api/chat`, `/api/session/reset`, `/health` | §4               |
| T-PY-02 | Implementar **6 repositoris** MySQL + normalitzador JSON         | §5               |
| T-PY-03 | Implementar `search_municipality_guides` + pipeline RAG          | §6               |
| T-PY-04 | Panell `/admin/guides` + API admin                               | §7               |
| T-PY-05 | System prompt: idioma, enllaços, routing 6 buscadors + guia      | RF-0211, RF-0302 |
| T-PY-06 | Rate limiting i logging                                          | §10, §11         |


### 2.4 Tasques Ops


| #        | Tasca                                                         |
| -------- | ------------------------------------------------------------- |
| T-OPS-01 | Crear usuari MySQL `agent_read` (SELECT només)                |
| T-OPS-02 | Exportar `docs/schema.sql` (estructura sense dades)           |
| T-OPS-03 | Provisió PostgreSQL staging/prod amb extensió **pgvector**    |
| T-OPS-04 | Docker amb contenidor **Python**; PostgreSQL extern recomanat |
| T-OPS-05 | Variables `.env` i xarxa PHP ↔ Python ↔ MySQL                 |
| T-OPS-06 | Backups PostgreSQL + carpeta `data/guides/`                   |


---

## 3. Integració web (PHP)

### 3.1 Widget de xat


| Element      | Especificació                                                               |
| ------------ | --------------------------------------------------------------------------- |
| Posició      | Globus fix, cantó inferior dret                                             |
| Comportament | Clic obre panell overlay; tancar amaga panell (sessió conservada)           |
| Client JS    | Reutilitzar lògica SSE de [app/static/js/chat.js](../app/static/js/chat.js) |
| Render       | Markdown (`marked`); enllaços obren nova pestanya (`target="_blank"`)       |


### 3.2 Reverse proxy

El navegador només parla amb `https://www.femturisme.cat`. Exemple nginx:

```nginx
location /api/chat {
    proxy_pass http://<HOST_AGENT>:<PORT>/api/chat;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
}
location /api/session/reset {
    proxy_pass http://<HOST_AGENT>:<PORT>/api/session/reset;
}
```

Headers recomanats al proxy: `X-Accel-Buffering: no` (SSE).

### 3.3 Context de pàgina (opcional v1)

Camp JSON opcional al body de `/api/chat`:

```json
{
  "message": "Què fer aquí?",
  "session_id": "uuid",
  "page_context": {
    "section": "agenda",
    "ubicacio": "Empordà",
    "municipality": "Pals"
  }
}
```

**Origen PHP:** extreure de la URL o variables de plantilla de la pàgina actual.

---

## 4. API pública del servei agent

Implementació de referència: [app/routes/api.py](../app/routes/api.py).

### 4.1 `POST /api/chat`

**Content-Type:** `application/json`  
**Response:** `text/event-stream` (SSE)

#### Request


| Camp           | Tipus  | Obligatori | Descripció                                         |
| -------------- | ------ | ---------- | -------------------------------------------------- |
| `message`      | string | Sí         | Text de l'usuari                                   |
| `session_id`   | string | No         | UUID de sessió; si falta, el servidor en genera un |
| `page_context` | object | No         | Context de pàgina (§3.3)                           |


**Errors HTTP:**


| Codi | Condició                |
| ---- | ----------------------- |
| 400  | `message` buit o absent |


#### Events SSE

Cada línia: `data: {JSON}\n\n`


| `type`        | Descripció        | Camps addicionals               |
| ------------- | ----------------- | ------------------------------- |
| `tool_call`   | Inici consulta    | `tool`, `input`                 |
| `tool_result` | Resultat consulta | `tool`, `result` (objecte JSON) |
| `text_chunk`  | Fragment resposta | `content` (string)              |
| `done`        | Fi del torn       | `full_text` (string complet)    |
| `error`       | Error             | `message`                       |


#### Exemple: «Què fem aquest cap de setmana a l'Empordà?»

**Request:**

```json
{
  "message": "Què fem aquest cap de setmana a l'Empordà?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Seqüència SSE (simplificada):**

```
data: {"type":"tool_call","tool":"search_events","input":{"destination":"Empordà","date_from":"2026-06-28","date_to":"2026-06-29"}}

data: {"type":"tool_result","tool":"search_events","result":{"destination":"Empordà","date_from":"2026-06-28","date_to":"2026-06-29","total":"12","results":[{"title":"Fira medieval de Pals","url":"https://www.femturisme.cat/agenda/fira-medieval-pals","date":"28 de juny","description":"..."}]}}

data: {"type":"text_chunk","content":"Aquest cap de setmana a l'Empordà tens diverses opcions: "}

data: {"type":"text_chunk","content":"**[Fira medieval de Pals](https://www.femturisme.cat/agenda/fira-medieval-pals)** — dissabte…"}

data: {"type":"done","full_text":"Aquest cap de setmana a l'Empordà tens diverses opcions: ..."}
```

**Notes:**

- Les dates `date_from`/`date_to` les infereix el servei agent des de «aquest cap de setmana».
- El text final ha d'incloure enllaços Markdown construïts a partir del camp `url` de cada resultat.
- v1 prototip: consulta via scraping temporal; **objectiu producció:** MySQL segons §5.

### 4.2 `POST /api/session/reset`

#### Request

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Response

```json
{
  "ok": true
}
```

Esborra l'historial en memòria per aquella sessió ([app/services/agent_service.py](../app/services/agent_service.py)).

### 4.3 `GET /health`

Healthcheck per a monitorització i desplegament.

**Response esperada:** HTTP 200 amb cos indicant estat del servei (implementació a acordar a Fase 1).

---

## 5. Serveis de consulta de catàleg (6 operacions)

**Objectiu v1:** SQL parametritzada a `app/db/repositories/*.py` documentada a [sql-mapeo.md](sql-mapeo.md).  
**Prototip actual:** 4 tools legacy + scraping ([app/services/tools/](../app/services/tools/)) — **pendent migració** al model de 6 dominis ([dominio-femturisme-ca.md](dominio-femturisme-ca.md) §6).

### Deprecació model antic


| Antic                              | Nou                                                                         |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `search_accommodations`            | `**search_establishments`** (dormir + menjar per `type`)                    |
| `search_experiences` (ofertes web) | `**search_experiences**` (experiències promocionals — significat redefinit) |


### 5.1 `search_establishments`


| Paràmetre     | Tipus  | Obligatori | Descripció                       |
| ------------- | ------ | ---------- | -------------------------------- |
| `destination` | string | Sí         | Comarca o municipi               |
| `type`        | string | No         | hotel, camping, restaurant, bar… |


**Repository:** `EstablishmentsRepository`  
**Taules MySQL:** TBD — hipòtesi `establiments`  
**URLs:** TBD (`/on-dormir/`, `/on-menjar/` o unificat)

### 5.2 `search_articles`


| Paràmetre     | Tipus  | Obligatori | Descripció                  |
| ------------- | ------ | ---------- | --------------------------- |
| `destination` | string | No         | Zona o població relacionada |
| `topic`       | string | No         | Tema (parc natural, festa…) |
| `query`       | string | No         | Text curt de cerca          |


**Repository:** `ArticlesRepository`  
**Taules MySQL:** TBD  
**URLs:** TBD

### 5.3 `search_destinations`


| Paràmetre     | Tipus  | Obligatori | Descripció                |
| ------------- | ------ | ---------- | ------------------------- |
| `destination` | string | Sí         | Població, municipi o lloc |
| `region`      | string | No         | Comarca o regió           |


**Repository:** `DestinationsRepository`  
**Taules MySQL:** TBD — poblacions / on anar  
**URLs:** TBD

### 5.4 `search_routes`


| Paràmetre     | Tipus  | Obligatori | Descripció     |
| ------------- | ------ | ---------- | -------------- |
| `destination` | string | Sí         | Comarca o zona |
| `type`        | string | No         | A peu, bici…   |


**Repository:** `RoutesRepository`  
**URL referència:** `https://www.femturisme.cat/rutes?ubicacio={destination}`  
**Prefix fitxa:** `https://www.femturisme.cat/rutes/{slug}`

### 5.5 `search_events` (agenda)


| Paràmetre     | Tipus  | Obligatori | Descripció         |
| ------------- | ------ | ---------- | ------------------ |
| `destination` | string | Sí         | Comarca o municipi |
| `date_from`   | string | No         | `YYYY-MM-DD`       |
| `date_to`     | string | No         | `YYYY-MM-DD`       |


**Repository:** `EventsRepository`  
**URL referència:** `https://www.femturisme.cat/agenda?ubicacio={destination}`  
**Prefix fitxa:** `https://www.femturisme.cat/agenda/{slug}`

**Nota:** Distint de `search_experiences` (RN-009).

### 5.6 `search_experiences` (promocionals)


| Paràmetre       | Tipus  | Obligatori | Descripció                 |
| --------------- | ------ | ---------- | -------------------------- |
| `destination`   | string | Sí         | Comarca o municipi         |
| `category`      | string | No         | Categoria opcional         |
| `establishment` | string | No         | Nom establiment relacionat |


**Repository:** `ExperiencesRepository`  
**Exemples:** dinar Sant Valentí, arrossada Olvan  
**Taules MySQL:** TBD — relació establiment/població  
**URLs:** TBD

### 5.7 Format JSON de sortida (comú a tots els buscadors)

#### Card (element de `results[]`)

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

#### Wrapper (exemple `search_events`)

```json
{
  "destination": "Empordà",
  "date_from": "2026-06-28",
  "date_to": "2026-06-29",
  "total": "12",
  "results": [],
  "error": null
}
```

En cas d'error de connexió:

```json
{
  "error": "No s'ha pogut accedir a les dades del catàleg",
  "results": []
}
```

### 5.8 Límits operatius


| Límit                                  | Valor v1                                 |
| -------------------------------------- | ---------------------------------------- |
| Files SQL màxim                        | 20 (`LIMIT` al repositori)               |
| Cards retornades al model per consulta | 6 (truncat al servei)                    |
| Iteracions de consulta per missatge    | 5 (`AGENT_MAX_TOOL_ITERATIONS`)          |
| Timeout connexió MySQL / HTTP          | 2 s SQL objectiu; 15 s scraping prototip |


---

## 6. Servei de consulta de guies PDF

### 6.1 Operació `search_municipality_guides`


| Paràmetre      | Tipus  | Obligatori | Descripció                                         |
| -------------- | ------ | ---------- | -------------------------------------------------- |
| `query`        | string | Sí         | Text de cerca dins les guies                       |
| `municipality` | string | Sí         | Municipi (filtre)                                  |
| `category`     | string | No         | Categoria opcional (restaurants, aparcament, etc.) |


**Flux:**

1. Generar embedding de la query.
2. Cerca vectorial a PostgreSQL (pgvector) filtrada per `municipality`.
3. Només chunks de documents amb `status = indexed`.
4. Retornar top-K fragments (K acordat, p.ex. 5).

#### JSON de sortida

```json
{
  "query": "on dinar plaça major",
  "municipality": "Berga",
  "total": 3,
  "results": [
    {
      "source": "Guia turística Berga 2024",
      "page": 12,
      "summary": "Fragment de text relevant…",
      "doc_id": "uuid"
    }
  ]
}
```

### 6.2 Pipeline d'indexació


| Pas   | Acció                                          | Estat BD                   |
| ----- | ---------------------------------------------- | -------------------------- |
| 1     | Pujada fitxer                                  | `pending`                  |
| 2     | Extracció text (pymupdf/pdfplumber)            | `extracting`               |
| 3     | Fragmentació (500–1000 tokens, overlap 10–15%) | `chunking`                 |
| 4     | Generació embeddings (API batch)               | `embedding`                |
| 5     | Upsert vectors + metadades                     | `indexed`                  |
| Error | Qualsevol pas                                  | `failed` + `error_message` |


**Fitxer PDF original:** `data/guides/{doc_id}/original.pdf` (disc del servidor agent).  
**No** es guarda el PDF dins PostgreSQL.

### 6.3 Taula `guide_documents` (PostgreSQL agent)


| Camp                    | Tipus         | Descripció                               |
| ----------------------- | ------------- | ---------------------------------------- |
| `doc_id`                | UUID PK       | Identificador                            |
| `title`                 | string        | Títol visible                            |
| `municipality`          | string        | Filtre RAG                               |
| `source_filename`       | string        | Nom original                             |
| `storage_path`          | string        | Ruta al disc                             |
| `status`                | enum          | `pending` … `indexed` / `failed`         |
| `error_message`         | text nullable | Motiu si `failed`                        |
| `pages_count`           | int           | Pàgines extretes                         |
| `chunks_count`          | int           | Fragments                                |
| `embedded_chunks_count` | int           | Ha de coincidir amb `chunks_count` si OK |
| `embedding_model`       | string        | Model usat                               |
| `indexed_at`            | timestamp     | Fi OK                                    |
| `version`               | int           | Increment en reindexar                   |


**Metadades per chunk al vector store:**

```json
{
  "doc_id": "uuid",
  "doc_title": "Guia turística Berga 2024",
  "municipality": "Berga",
  "page": 12,
  "chunk_index": 3,
  "embedding_model": "text-embedding-3-small",
  "indexed_at": "2026-06-23T10:00:00Z"
}
```

---

## 7. API d'administració de guies

Base path recomanada: `/admin/api/guides`  
UI HTML: `/admin/guides`, `/admin/guides/upload`, `/admin/guides/{doc_id}`


| Mètode | Ruta                                    | Descripció                                        |
| ------ | --------------------------------------- | ------------------------------------------------- |
| POST   | `/admin/api/guides/upload`              | Pujada multipart: `file`, `municipality`, `title` |
| GET    | `/admin/api/guides`                     | Llistat JSON de documents                         |
| GET    | `/admin/api/guides/{doc_id}`            | Detall d'un document                              |
| POST   | `/admin/api/guides/{doc_id}/reindex`    | Reexecutar pipeline                               |
| POST   | `/admin/api/guides/{doc_id}/smoke-test` | Prova cerca amb query fixa o paramètre            |


### 7.1 Formulari de pujada


| Camp           | Tipus      | Obligatori |
| -------------- | ---------- | ---------- |
| `file`         | file (PDF) | Sí         |
| `municipality` | string     | Sí         |
| `title`        | string     | Sí         |


**Response exitosa:** HTTP 201 amb `doc_id` i estat inicial `pending`.

### 7.2 Seguretat panell

- Accés per VPN / IP allowlist.
- Autenticació HTTP Basic, token o SSO intern (decidir a desplegament).
- `robots.txt` / cap enllaç des del web públic.

---

## 8. Model de dades

### 8.1 MySQL femturisme (existent)


| Aspecte                 | Detall                                              |
| ----------------------- | --------------------------------------------------- |
| Rol                     | Font de veritat del catàleg web                     |
| Accés agent             | Usuari `agent_read`, permís **SELECT** només        |
| Esquema                 | Documentat a `docs/schema.sql` (DDL sense dades)    |
| Canvis v1               | **Cap** esquema nou a MySQL; només usuari read-only |
| Implementació consultes | SQL fixa per operació; mapatge a JSON §5.5          |


### 8.2 PostgreSQL agent (nou)


| Aspecte    | Detall                                                |
| ---------- | ----------------------------------------------------- |
| Rol        | Metadades PDF, chunks, vectors                        |
| Accés      | Usuari `agent_app` read/write                         |
| Extensió   | `pgvector`                                            |
| Hosting    | **Extern gestionat** recomanat (Supabase, Neon, RDS…) |
| Escriptors | Només servei Python                                   |


**No barrejar:** MySQL no guarda PDFs ni vectors. PostgreSQL no toca el catàleg de la web.

---

## 9. Seguretat


| Mesura              | Detall                                                                                |
| ------------------- | ------------------------------------------------------------------------------------- |
| MySQL read-only     | Usuari sense INSERT/UPDATE/DELETE                                                     |
| SQL parametritzada  | Consultes fixes al codi; **no** SQL generada per IA en producció (decisió tancada v1) |
| Allowlist implícita | Només **6** operacions de catàleg + guies; sense accés SQL arbitrari                  |
| Rate limiting       | Límit de peticions a `/api/chat` per IP/sessió (Fase 8)                               |
| Secrets             | Claus API LLM i embeddings només a `.env`, no al repo                                 |
| Admin               | Panell no públic; PDFs no indexables                                                  |
| XSS                 | Escapar HTML al client; Markdown amb enllaços controlats                              |


Decisió arquitectònica SQL vs text-to-SQL (referència opcional): [text-to-sql-desventajas.md](text-to-sql-desventajas.md).

---

## 10. Entorns i configuració

### 10.1 Entorns


| Entorn        | MySQL                          | PostgreSQL        | Servei Python  | Widget             |
| ------------- | ------------------------------ | ----------------- | -------------- | ------------------ |
| **Staging**   | BD staging o read-only replica | Instància staging | Docker staging | femturisme staging |
| **Producció** | MySQL prod read-only           | Instància prod    | Docker prod    | femturisme.cat     |


No indexar PDFs de prova a producció.

### 10.2 Variables d'entorn principals

```env
# Agent
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
AGENT_MAX_TOOL_ITERATIONS=5

# MySQL femturisme (read-only)
MYSQL_HOST=...
MYSQL_PORT=3306
MYSQL_USER=agent_read
MYSQL_PASSWORD=...
MYSQL_DATABASE=femturisme

# PostgreSQL agent
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_USER=agent_app
POSTGRES_PASSWORD=...
POSTGRES_DATABASE=agent_femturisme

# Embeddings
OPENAI_API_KEY=...
EMBEDDING_MODEL=text-embedding-3-small
```

### 10.3 Docker (staging/producció recomanat)

```yaml
services:
  agent:
    build: .
    ports:
      - "5000:5000"
    env_file: .env
    volumes:
      - ./data/guides:/app/data/guides
# PostgreSQL: NO al Docker de prod — URL externa al .env
```

Dev local opcional: contenidor `postgres` amb imatge `pgvector/pgvector`.

---

## 11. Observabilitat i operació

### 11.1 Logging mínim


| Esdeveniment     | Camps                                              |
| ---------------- | -------------------------------------------------- |
| Request xat      | `session_id`, durada total                         |
| Consulta catàleg | nom operació, paràmetres, latència SQL, fila count |
| Consulta guia    | `municipality`, latència vector                    |
| Ingest PDF       | `doc_id`, pas, durada, error                       |
| Error            | stack trace, `session_id` o `doc_id`               |


### 11.2 Backups


| Recurs                        | Freqüència                        |
| ----------------------------- | --------------------------------- |
| PostgreSQL (panell proveïdor) | Automàtic diari                   |
| `data/guides/`                | Incloure en backup servidor agent |


### 11.3 Runbooks breus


| Incidència         | Acció                                                                      |
| ------------------ | -------------------------------------------------------------------------- |
| PDF `failed`       | Llegir `error_message` al panell → Reindexar → contactar dev si persisteix |
| MySQL inaccessible | Verificar xarxa/credencials; xat mostra error amigable                     |
| Query lenta        | EXPLAIN a staging; revisar índexs; confirmar LIMIT                         |
| Embedding API down | Documents queden a `failed`; reintentar quan servei recuperi               |


---

## 12. Pla de proves tècnic

Vinculat als CA de [especificacio-funcional-ca.md](especificacio-funcional-ca.md) §9.

### 12.1 Tests SQL automatitzats

Ubicació prevista: `tests/sql/`  
Font de casos: taules § casos de prova a [sql-mapeo.md](sql-mapeo.md)


| Test   | Paràmetres                             | Assert                            |
| ------ | -------------------------------------- | --------------------------------- |
| SQL-01 | destination=Girona, type=hotel         | ≥0 files establiments, URL vàlida |
| SQL-02 | destination=Pals, type=restaurant      | ≥0 files menjar                   |
| SQL-03 | topic=Parc Natural Cadí                | ≥0 articles                       |
| SQL-04 | destination=Besalú                     | ≥0 poblacions/on anar             |
| SQL-05 | destination=Empordà, dates cap setmana | files agenda dins interval        |
| SQL-06 | destination=Olvan                      | ≥0 experiències                   |
| SQL-07 | destination=Empordà, type=A peu        | ≥1 ruta                           |


### 12.2 Tests API


| Test   | Descripció                                                              | CA      |
| ------ | ----------------------------------------------------------------------- | ------- |
| API-01 | POST `/api/chat` missatge buit → 400                                    | —       |
| API-02 | SSE conté `done` després de pregunta simple                             | CA-0102 |
| API-03 | Pregunta catàleg → seqüència `tool_call` + `tool_result` + `text_chunk` | CA-0201 |
| API-04 | POST `/api/session/reset` → historial buit                              | CA-0105 |


### 12.3 Tests integració / UAT


| Lot       | N       | Descripció                        | CA           |
| --------- | ------- | --------------------------------- | ------------ |
| Catàleg   | 12      | 2 proves per domini (6 buscadors) | CA-0201–0207 |
| Guies     | 10      | Municipis amb PDF indexat         | CA-0301–0303 |
| Mixtes    | 10      | Catàleg + guia mateix municipi    | CA-0303      |
| **Total** | **~30** | Routing correcte ≥80%             | UAT-4        |


### 12.4 Tests admin PDF


| Test                              | CA      |
| --------------------------------- | ------- |
| Pujada → `indexed`                | CA-0401 |
| Reindexar després de `failed`     | CA-0403 |
| Smoke-test retorna chunks del doc | CA-0404 |


### 12.5 Tests PHP (manual o E2E)


| Test                           | CA      |
| ------------------------------ | ------- |
| Globus visible home + interior | CA-0101 |
| Proxy sense CORS               | CA-0106 |
| Mobile Safari / Chrome Android | RNF-008 |


---

## 13. Decisions tècniques

### 13.1 Tancades v1


| Decisió                           | Detall                                   |
| --------------------------------- | ---------------------------------------- |
| Consultes catàleg parametritzades | **6** buscadors SQL fixa; no text-to-SQL |
| Widget same-origin                | Proxy des de femturisme.cat              |
| Panell admin al Python            | No al CMS PHP                            |
| MySQL només lectura               | Usuari `agent_read`                      |
| PostgreSQL extern gestionat       | Recomanat staging/prod                   |


### 13.2 Pendents (no bloquegen aquesta especificació)


| Tema                                   | Opcions                                     |
| -------------------------------------- | ------------------------------------------- |
| Hosting Python                         | Mateixa màquina que PHP vs servidor dedicat |
| Model LLM / embedding producció        | Anthropic, OpenAI, etc.                     |
| Persistència historial multi-instància | Redis/PostgreSQL sessions                   |
| Vector store alternatiu                | pgvector vs Qdrant + PostgreSQL             |


---

## 14. Referències


| Document                                                       | Contingut                               |
| -------------------------------------------------------------- | --------------------------------------- |
| [dominio-femturisme-ca.md](dominio-femturisme-ca.md)           | Model de negoci, 6 dominis              |
| [especificacio-funcional-ca.md](especificacio-funcional-ca.md) | Requeriments, CU, CA, UAT               |
| [plan-integracion-ca.md](plan-integracion-ca.md)               | Pla per fases (equip intern)            |
| [sql-mapeo.md](sql-mapeo.md)                                   | Queries MySQL per operació              |
| [agente.md](agente.md)                                         | Bucle agent, proveïdors LLM             |
| [scraping-y-respuestas.md](scraping-y-respuestas.md)           | Prototip scraping (referència temporal) |
| [fase-3-tools-mysql-ca.md](fase-3-tools-mysql-ca.md)           | Guia implementació repositoris          |
