# DOCUMENT 03 - DISSENY TÈCNIC

## Plataforma d'Agents Intel·ligents de femturisme

| Camp | Valor |
|------|-------|
| Versió | 2.1 |
| Data | 2026-07-02 |
| Document base | AI agent-disseny-tecnic.docx |
| Font tècnica integrada | AI agent(1).docx |
| Audiència | Desenvolupadors, consultora tècnica, operacions |
| Estat | Esborrany refactoritzat per revisió tècnica |

Aquest document refactoritza la documentació tècnica existent. Conserva les decisions i detalls d'implementació definits al material original, els reordena en una estructura coherent i incorpora les decisions funcionals consensuades: motor únic, dos contextos operatius (mode femturisme / mode entitat), base de coneixement per entitats i gestió documental des del backend de femturisme.

Documents relacionats: [requeriments.md](requeriments.md), [funcional.md](funcional.md), [postgre_schema.md](../postgre_schema.md).

## Índex

- [1. Objectiu](#1-objectiu)
- [2. Decisions arquitectòniques](#2-decisions-arquitectòniques)
- [3. Arquitectura general](#3-arquitectura-general)
- [4. Arquitectura software i integració web](#4-arquitectura-software-i-integració-web)
- [5. Motor de l'Agent](#5-motor-de-lagent)
- [6. Sistema de Tools](#6-sistema-de-tools)
- [7. Base de Coneixement d'Entitats](#7-base-de-coneixement-dentitats)
- [8. Persistència de dades](#8-persistència-de-dades)
- [9. API REST](#9-api-rest)
- [10. Configuració](#10-configuració)
- [11. Desplegament](#11-desplegament)
- [12. Seguretat](#12-seguretat)
- [13. Observabilitat i operació](#13-observabilitat-i-operació)
- [14. Pla de proves](#14-pla-de-proves)
- [15. Pla d'implementació](#15-pla-dimplementació)
- [16. Decisions pendents i annexos](#16-decisions-pendents-i-annexos)

---

## 1. Objectiu

### 1.1 Finalitat

Aquest document descriu el disseny tècnic de la plataforma d'agents intel·ligents desenvolupada per femturisme.

El seu objectiu és definir l'arquitectura del sistema, els components que la formen, les tecnologies emprades i els mecanismes d'integració necessaris per implementar l'agent d'intel·ligència artificial.

El document està orientat a desenvolupadors i operacions. Ha de servir com a guia d'implementació, manteniment, desplegament i evolució de la plataforma.

### 1.2 Abast

Aquest document descriu:

- arquitectura de la plataforma;
- components software;
- integració amb femturisme.cat;
- API pública del servei agent;
- sistema de Tools i Repositories;
- gestió documental i indexació;
- model de dades MySQL i PostgreSQL;
- configuració per entorns;
- desplegament amb Docker;
- seguretat;
- observabilitat i pla de proves.

No descriu els requisits funcionals ni el comportament conversacional detallat de l'agent, que es documenten als documents de Presa de Requeriments i Disseny Funcional.

### 1.3 Criteris de refactorització

- Conservar les decisions tècniques del document original quan siguin vàlides.
- Eliminar duplicats i marcadors incomplets.
- Unificar la nomenclatura: Tool, Repository, Service, Controller/API.
- Separar clarament funcional, arquitectura i implementació.
- Marcar com a pendent allò que depèn de schema MySQL, hosting o decisió de desplegament.

---

## 2. Decisions arquitectòniques

| ID | Decisió | Estat | Justificació |
|----|---------|-------|--------------|
| ADR-001 | Motor únic d'agent | Acceptada | El mateix motor dona servei a femturisme, ajuntaments, poblacions i fires mitjançant context operatiu i configuració. |
| ADR-002 | Arquitectura basada en Tools | Acceptada | El model d'IA només accedeix a la informació mitjançant eines controlades. |
| ADR-003 | SQL parametritzada | Acceptada | No es permet SQL lliure generat pel model. Les consultes són fixes i revisables. |
| ADR-004 | MySQL només lectura | Acceptada | L'agent només consulta el catàleg. No escriu ni modifica contingut del portal. |
| ADR-005 | PostgreSQL + pgvector | Acceptada | Base documental, fragments i embeddings per a cerca semàntica. |
| ADR-006 | Base documental separada del catàleg | Acceptada | Els documents indexats per entitat no es guarden a MySQL del portal. |
| ADR-007 | Iteracions configurables | Acceptada | AGENT_MAX_TOOL_ITERATIONS limita bucles i controla temps/cost. Valor inicial: 5. |
| ADR-008 | Proxy same-origin | Acceptada | El navegador parla amb femturisme.cat; PHP/proxy reenvia cap al servei Python. |
| ADR-009 | Base de coneixement d'entitat prioritària | Acceptada | En mode entitat, la documentació de l'entitat activa té prioritat. En mode femturisme, només si l'element consultat té entity_id (Fase producte 2). |
| ADR-010 | Admin documental al backend femturisme | Acceptada | La UI de gestió documental s'integra al backend existent; el servei agent exposa APIs i pipeline. |
| ADR-011 | Enllaç portal ↔ entitat només al MySQL | Acceptada | L'associació entity_id a fitxes del catàleg es defineix al CMS/MySQL; PostgreSQL no manté mapatge invers de fitxes. |

### 2.1 No text-to-SQL en producció

La decisió tècnica és utilitzar Tools parametritzades i Repositories amb SQL fixa, no una Tool genèrica d'execució SQL. El LLM tria una Tool i genera paràmetres; el backend executa SQL revisada i normalitza la resposta.

Aquesta decisió redueix riscos de seguretat, evita exposar l'schema legacy al model, facilita proves automatitzades i manté el rendiment sota control.

---

## 3. Arquitectura general

### 3.1 Flux lògic d'un missatge

1. El navegador envia POST /api/chat al domini femturisme.cat, que actua com a proxy cap al servei Python.
2. El servei agent interpreta la pregunta amb el model LLM i decideix quines consultes executar.
3. Les consultes de catàleg llegeixen MySQL mitjançant SQL parametritzada.
4. Les consultes documentals llegeixen PostgreSQL + pgvector.
5. El servei agent genera la resposta final i l'emet per SSE al client.
6. El widget JS renderitza text en Markdown i enllaços.

### 3.2 Diagrama lògic

```text
Usuari
   |
   v
 Widget conversa femturisme.cat
   |
   v
 Backend PHP / reverse proxy
   |
   v
 Servei Agent Python
   |
   +--> Motor de l'Agent / LLM / Tool Calling
        |
        +--> Tools catàleg --> Repositories --> MySQL femturisme (read-only)
        |
        +--> Tool coneixement entitat --> DocumentsRepository --> PostgreSQL + pgvector (entities, guide_documents, document_chunks)
        |
        +--> Gestor context / sessions
```

### 3.3 Components principals

| Component | Responsabilitat | Tecnologia / ubicació |
|-----------|-----------------|----------------------|
| Widget web | Interfície de conversa, render Markdown, streaming SSE. | JS/CSS integrat al portal. |
| Backend femturisme | Proxy same-origin, context de pàgina, agent_context, gestió d'entitats i documents UI. | PHP existent. |
| Servei agent | API xat, Tool Calling, Repositories, pipeline documental. | Python + Flask. |
| MySQL femturisme | Font de veritat del catàleg web. | MySQL existent, SELECT only. |
| PostgreSQL agent | Entitats, documents, chunks, vectors i metadades. | PostgreSQL + pgvector. |
| LLM | Interpretació, planificació i generació de resposta. | Anthropic via LLM_PROVIDER=anthropic. |
| Embeddings | Vectorització de consultes i documents. | OpenAI text-embedding-3-small. |

---

## 4. Arquitectura software i integració web

### 4.1 Stack tecnològic

| Component | Tecnologia |
|-----------|------------|
| Frontend | Widget integrat a femturisme.cat |
| Backend portal | PHP (aplicació existent) |
| Motor IA | Python |
| Framework API | Flask |
| Model LLM | Anthropic Claude (configurable) |
| Embeddings | OpenAI text-embedding-3-small |
| Base de dades portal | MySQL read-only |
| Base documental | PostgreSQL + pgvector |
| Contenidors | Docker |
| Dependències | pip + requirements.txt |

### 4.2 Estructura del projecte Python

```text
agent/
  app/
    routes/            # API Flask: /api/chat, /api/session/reset, /health, admin API
    services/          # Agent service, document service, embedding service
    services/tools/    # Implementació de Tools exposades al LLM
    db/repositories/   # Repositories MySQL i PostgreSQL
    prompts/           # System prompts i plantilles
    static/js/         # Widget reutilitzable / xat
    static/admin/      # Recursos admin si cal
    config/            # Configuració d'aplicació
  data/guides/         # PDF original: data/guides/{doc_id}/original.pdf
  tests/sql/           # Tests d'integració SQL
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env
```

### 4.3 Repartiment de responsabilitats

| Equip / component | Tasques |
|-------------------|---------|
| PHP / mantenedor web | Globus i panell de xat, include al layout global, proxy /api/chat, proxy /api/session/reset, page_context, agent_context, estils, gestor d'entitats i documental al backend. |
| Servei agent Python | API xat, 6 Tools MySQL, search_entity_knowledge, EntitiesRepository, DocumentsRepository, pipeline RAG, connexions BD, system prompt per mode, logging i rate limiting. |
| Operacions | Usuari MySQL read-only, PostgreSQL amb pgvector, Docker, .env, firewall, backups, xarxa PHP-Python-MySQL. |
| Femturisme | Validació de respostes, documents de prova, aclariment schema MySQL i URLs canòniques. |

### 4.4 Tasques PHP

| ID | Tasca |
|----|-------|
| T-PHP-01 | Incrustar globus + panell JS/CSS al layout global. |
| T-PHP-02 | Configurar reverse proxy /api/chat i /api/session/reset cap al host Python. |
| T-PHP-03 | Enviar page_context opcional al body de /api/chat. |
| T-PHP-04 | Botó "Nova conversa" cridant /api/session/reset. |
| T-PHP-05 | Proves desktop/mòbil en staging. |
| T-PHP-06 | Afegir gestor d'entitats i gestor documental al backend de femturisme (CRUD entitats + documents per entity_id). |

### 4.5 Tasques Python

| ID | Tasca |
|----|-------|
| T-PY-01 | Desplegar Flask amb /api/chat, /api/session/reset i /health. |
| T-PY-02 | Implementar 6 Repositories MySQL + normalitzador JSON. |
| T-PY-03 | Implementar search_entity_knowledge + pipeline RAG (EntitiesRepository, DocumentsRepository). |
| T-PY-04 | Exposar API admin entitats: create, list, detail, update, delete. |
| T-PY-05 | Exposar API admin documents: upload, list, detail, reindex, delete, smoke-test. |
| T-PY-06 | System prompt: idioma, enllaços, routing Tools, modes operatius i fonts per entitat. |
| T-PY-07 | Rate limiting, logging i mètriques bàsiques. |

### 4.6 Tasques Ops

| ID | Tasca |
|----|-------|
| T-OPS-01 | Crear usuari MySQL agent_read amb SELECT només. |
| T-OPS-02 | Exportar docs/schema.sql amb estructura sense dades. |
| T-OPS-03 | Provisió PostgreSQL staging/prod amb extensió pgvector. |
| T-OPS-04 | Docker amb contenidor Python; PostgreSQL extern recomanat. |
| T-OPS-05 | Configurar xarxa PHP -> Python -> MySQL/PostgreSQL. |
| T-OPS-06 | Backups PostgreSQL + carpeta data/guides/. |

### 4.7 Widget de xat

| Element | Especificació |
|---------|---------------|
| Posició | Globus fix al cantó inferior dret. |
| Comportament | Clic obre panell overlay; tancar amaga panell i conserva sessió. |
| Client JS | Reutilitzar lògica SSE de app/static/js/chat.js. |
| Render | Markdown amb marked; enllaços amb target="_blank". |

### 4.8 Reverse proxy

El navegador només ha de comunicar-se amb https://www.femturisme.cat. El backend/proxy reenvia les peticions al servei Python.

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

Headers recomanats per SSE: X-Accel-Buffering: no. Cal definir timeout de proxy i autenticació interna entre PHP i Python en desplegament.

### 4.9 Context de pàgina i context operatiu

El PHP (o el widget d'entitat) envia context opcional en cada crida a /api/chat.

- **page_context** — ajuda a resoldre preguntes ambigües segons la pàgina actual del portal.
- **agent_context** — determina el mode operatiu i les fonts permeses.

```json
{
  "message": "Què fer aquí?",
  "session_id": "uuid",
  "page_context": {
    "section": "agenda",
    "ubicacio": "Empordà",
    "municipality": "Pals"
  },
  "agent_context": {
    "mode": "femturisme",
    "entity_id": null
  }
}
```

Exemple mode entitat (xat propi d'un client):

```json
{
  "message": "Quins horaris té el museu?",
  "session_id": "uuid",
  "agent_context": {
    "mode": "entitat",
    "entity_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

Modes operatius (RF-14):

| Mode | Fonts permeses |
|------|----------------|
| Mode femturisme | 6 Tools MySQL del catàleg + search_entity_knowledge només si el flux detecta entity_id (Fase producte 2) |
| Mode entitat | Només search_entity_knowledge de l'entity_id indicada; sense catàleg global salvo decisió explícita futura |

El motor filtra les Tools exposades al LLM segons agent_context.mode abans de cada torn.

---

## 5. Motor de l'Agent

### 5.1 Responsabilitats

- interpretar la consulta de l'usuari;
- recuperar el context de conversa;
- identificar context operatiu;
- seleccionar les Tools necessàries;
- coordinar iteracions de consulta;
- construir el prompt final;
- generar la resposta;
- actualitzar el context.

El Motor de l'Agent no executa SQL, no accedeix directament a MySQL/PostgreSQL, no genera embeddings i no gestiona documents. Aquestes funcions corresponen a Tools, Repositories i serveis especialitzats.

### 5.2 Flux de processament

```text
Recepció consulta
   -> Carregar context
   -> Construcció del prompt
   -> LLM
   -> Tool Calling
   -> Tool Manager
   -> Execució Tools
   -> Resultats
   -> LLM
   -> Resposta
   -> Actualització context
```

### 5.3 Prompt i context

Abans de cada iteració es construeix el prompt del model. Incorpora: missatge de l'usuari, historial rellevant, idioma, agent_context (mode + entity_id), page_context, definició de Tools filtrades per mode, instruccions del sistema (identitat femturisme vs identitat entitat des de entities.config).

### 5.4 Tool Calling i iteracions

El model pot executar diverses iteracions abans de generar la resposta definitiva. Cada iteració permet analitzar resultats, decidir si cal una altra Tool i combinar fonts diferents.

```env
AGENT_MAX_TOOL_ITERATIONS=5
```

El valor inicial és 5 iteracions per consulta. Quan s'assoleix el límit, el motor finalitza la consulta i construeix la millor resposta possible amb la informació disponible.

### 5.5 Finalització

- el model disposa de la informació necessària;
- no hi ha més Tools aplicables;
- s'assoleix AGENT_MAX_TOOL_ITERATIONS;
- es produeix un error irrecuperable.

### 5.6 Flux condicional catàleg → coneixement entitat (mode femturisme, Fase producte 2)

1. Tool de catàleg retorna card amb entity_id (prové del MySQL/CMS).
2. El motor invoca search_entity_knowledge amb aquell entity_id.
3. Combina catàleg estructurat + fragments documentals en la resposta.

En mode entitat aquest flux no aplica: entity_id ja ve fixat a agent_context.

---

## 6. Sistema de Tools

### 6.1 Objectiu

El Sistema de Tools proporciona al Motor de l'Agent un mecanisme estandarditzat per accedir a les fonts d'informació. Les Tools retornen dades estructurades i no generen text final per a l'usuari.

### 6.2 Arquitectura

```text
Motor Agent
   -> Tool Manager
     -> Tool
       -> Repository
         -> MySQL / PostgreSQL
       <- Resultats normalitzats
     <- JSON Tool
   <- Context per al LLM
```

### 6.3 Contracte comú d'una Tool

| Element | Descripció |
|---------|------------|
| name | Nom estable exposat al LLM. No s'ha de canviar sense actualitzar prompt i proves. |
| description | Descripció funcional clara perquè el model pugui decidir quan usar-la. |
| parameters | Schema d'entrada amb tipus, camps obligatoris i valors permesos. |
| validation | Validació abans d'executar cap consulta. |
| repository | Mòdul que encapsula accés a dades. |
| response | JSON normalitzat segons el contracte comú. |
| errors | Error controlat, mai stack trace al LLM ni a l'usuari. |
| timeout | Límit d'execució per evitar bloquejos. |

### 6.4 Catàleg de Tools v1

| Tool | Repository | BD | Funció |
|------|------------|-----|--------|
| search_establishments | EstablishmentsRepository | MySQL | Establiments: on dormir, on menjar i què fer. |
| search_articles | ArticlesRepository | MySQL | Articles i notícies editorials. |
| search_destinations | DestinationsRepository | MySQL | Poblacions, comarques i llocs. |
| search_routes | RoutesRepository | MySQL | Itineraris i rutes. |
| search_events | EventsRepository | MySQL | Agenda d'esdeveniments amb data. |
| search_experiences | ExperiencesRepository | MySQL | Experiències promocionals lligades a establiment o població. |
| search_entity_knowledge | DocumentsRepository | PostgreSQL + pgvector | Base de coneixement documental d'una entitat (alias legacy: search_municipality_guides). |

### 6.5 Migració des del model antic

| Model antic | Model nou | Acció |
|-------------|-----------|-------|
| search_accommodations | search_establishments | Fusionar dormir + menjar; filtre type. |
| search_experiences (ofertes web) | search_experiences | Redefinir com experiències promocionals. |
| search_events | search_events | Mantenir nom i reforçar definició d'agenda. |
| search_routes | search_routes | Mantenir nom. |
| - | search_articles | Nova Tool. |
| - | search_destinations | Nova Tool. |
| search_municipality_guides | search_entity_knowledge | Renombrar; paràmetre entity_id en lloc de municipality. |

El prototip actual encara pot contenir 4 Tools legacy + scraping. Objectiu v1: 6 Tools MySQL + search_entity_knowledge segons aquest document.

### 6.5b Restricció de Tools per mode operatiu

| Mode | Restricció |
|------|------------|
| Mode femturisme | 6 Tools MySQL + search_entity_knowledge (condicional per entity_id) |
| Mode entitat | Només search_entity_knowledge (entity_id = agent_context.entity_id) |

### 6.6 Tool: search_establishments

Cerca d'establiments turístics per zona i tipus: allotjament, restauració i altres serveis.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | EstablishmentsRepository |
| Font de dades | MySQL |
| Taules MySQL | `establiment_general`, `establiment_continguts`, `establiment_tipus`, `generic_tipus_establiment`, `establiment_pobles`, `poble_*` — veure [sql-mapeo.md §1](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/establiments/{param_url}` (prefix fix; veure [sql-mapeo.md §URLs](../sql-mapeo.md)) |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | Sí | Comarca o municipi |
| type | string | No | hotel, camping, restaurant, bar... |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant EstablishmentsRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.7 Tool: search_articles

Consulta d'articles o notícies sobre poblacions, esdeveniments, parcs naturals i temes del portal.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | ArticlesRepository |
| Font de dades | MySQL |
| Taules MySQL | `noticia_general`, `noticia_continguts`, `noticia_pobles`, `poble_*` — veure [sql-mapeo.md §2](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/noticies/{param_url}` (hipòtesi dev validada; confirmació client pendent) |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | No | Zona o població relacionada |
| topic | string | No | Tema: parc natural, festa, etc. |
| query | string | No | Text lliure curt |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant ArticlesRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.8 Tool: search_destinations

Consulta d'informació sobre pobles, municipis, comarques i llocs per visitar.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | DestinationsRepository |
| Font de dades | MySQL |
| Taules MySQL | `poble_general`, `poble_continguts`, `poble_comarques`, `generic_ubicacions` — veure [sql-mapeo.md §3](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/pobles/{param_url}` |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | Sí | Població, municipi o lloc |
| region | string | No | Comarca o regió |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant DestinationsRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.9 Tool: search_routes

Consulta d'itineraris turístics per zona i modalitat.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | RoutesRepository |
| Font de dades | MySQL |
| Taules MySQL | `ruta_general`, `ruta_continguts`, `ruta_pobles`, `ruta_tematica`, `generic_tematiques`, `poble_*` — veure [sql-mapeo.md §4](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/rutes/{param_url}` |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | Sí | Comarca o zona |
| type | string | No | A peu, bici... |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant RoutesRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.10 Tool: search_events

Consulta d'esdeveniments de calendari: fires, concerts, festes i activitats programades.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | EventsRepository |
| Font de dades | MySQL |
| Taules MySQL | `agenda_general`, `agenda_continguts`, `agenda_dates`, `agenda_pobles`, `poble_*` — veure [sql-mapeo.md §5](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/agenda/{param_url}` |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | Sí | Comarca o municipi |
| date_from | string | No | YYYY-MM-DD |
| date_to | string | No | YYYY-MM-DD |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant EventsRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.11 Tool: search_experiences

Consulta d'activitats promocionals lligades a un establiment o una població. No substitueix agenda.

#### Metadades

| Camp | Valor |
|------|-------|
| Repository | ExperiencesRepository |
| Font de dades | MySQL |
| Taules MySQL | `oferta_general`, `oferta_continguts`, `oferta_categories`, `generic_categoria_oferta`, `establiment_*`, `poble_*` — veure [sql-mapeo.md §6](../sql-mapeo.md) |
| URL fitxa | `https://www.femturisme.cat/ofertes/{param_url}` (hipòtesi dev validada; confirmació client pendent) |

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| destination | string | Sí | Comarca o municipi |
| category | string | No | Categoria opcional |
| establishment | string | No | Nom establiment relacionat |

#### Procés

1. Validar paràmetres.
2. Executar consulta mitjançant ExperiencesRepository.
3. Aplicar filtres de publicació/vigència segons domini.
4. Normalitzar resultats al format JSON comú.
5. Retornar JSON al Motor de l'Agent.

#### Errors

- sense resultats;
- paràmetres invàlids;
- error de connexió amb MySQL;
- timeout de consulta.

### 6.12 Tool: search_entity_knowledge

Consulta semàntica a la base de coneixement documental d'una entitat (ajuntament, museu, club, diputació…).

#### Paràmetres

| Paràmetre | Tipus | Obligatori | Descripció |
|-----------|-------|------------|------------|
| query | string | Sí | Text de cerca dins els documents indexats. |
| entity_id | UUID | Sí | Identificador de l'entitat (entities.entity_id). |
| category | string | No | Categoria opcional: patrimoni, festes, museu, etc. |
| limit | integer | No | Nombre màxim de fragments (default acordat al servei). |

#### Flux

1. Validar entity_id actiu (entities.is_active).
2. Generar embedding de la query.
3. Cerca vectorial a document_chunks filtrada per entity_id.
4. Només chunks de documents amb guide_documents.status = indexed.
5. Retornar top-K fragments amb source, page, summary, doc_id, entity_id.

### 6.13 Format JSON comú de sortida

Totes les Tools de catàleg retornen una llista de cards normalitzades dins un wrapper específic de la consulta.

Card (element de results[]):

```json
{
  "id": "string | null",
  "type": "string | null",
  "title": "string",
  "location": "string | null",
  "description": "string | null",
  "url": "string | null",
  "image": "string | null",
  "date": "string | null",
  "entity_id": "uuid | null"
}
```

**entity_id** — opcional; prové del MySQL quan la fitxa del portal té associació a una entitat (RF-15, Fase producte 2). El motor el fa servir per invocar search_entity_knowledge en mode femturisme.

Exemple de wrapper per search_events:

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

### 6.14 Límits operatius

| Límit | Valor v1 |
|-------|----------|
| Files SQL màxim | 20 (LIMIT al Repository) |
| Cards retornades al model per consulta | 6 (truncat al servei) |
| Iteracions de consulta per missatge | 5 (AGENT_MAX_TOOL_ITERATIONS) |
| Timeout connexió MySQL / HTTP | 2 s SQL objectiu; 15 s scraping prototip |
| Escriptura MySQL | No permesa |

---

## 7. Base de Coneixement d'Entitats

### 7.1 Objectiu

Cada entitat (ajuntament, museu, club, diputació, establiment, fira…) pot tenir una base de coneixement pròpia: documents indexats que complementen el catàleg estructurat de femturisme.cat.

Prioritat segons mode operatiu (funcional.md §13):

- Mode entitat: base de coneixement de l'entitat activa.
- Mode femturisme: catàleg primer; base d'entitat només si entity_id associat (Fase producte 2).

### 7.2 Gestió des del backend de femturisme

La gestió s'integra al backend de femturisme (ADR-010). Funcionalitats mínimes (RF-13):

| Funcionalitat | Descripció |
|---------------|------------|
| Crear / editar / eliminar entitat | CRUD d'entitats amb entity_id estable (UUID). |
| Pujar document | Carrega fitxer PDF vinculat a entity_id. |
| Llistar documents | Documents per entitat amb estat d'indexació. |
| Consultar estat | pending, extracting, chunking, embedding, indexed, failed. |
| Eliminar document | Elimina fitxer, metadades i vectors. |
| Reindexar | Reexecuta el pipeline sobre l'original al disc. |
| Smoke-test | Prova cerca search_entity_knowledge sobre el document. |

### 7.3 Emmagatzematge del fitxer

El PDF original no es guarda dins PostgreSQL ni MySQL. Es desa al disc del servidor agent:

```text
data/guides/{doc_id}/original.pdf
```

A PostgreSQL es desen metadades, text fragmentat i vectors. Mantenir el PDF original permet reindexar quan canviï el model d'embedding o el chunking.

### 7.4 Pipeline d'indexació

| Pas | Acció | Estat BD |
|-----|-------|----------|
| 1 | Pujada del fitxer | pending |
| 2 | Extracció de text amb pymupdf/pdfplumber | extracting |
| 3 | Fragmentació en chunks de 500-1000 tokens amb overlap 10-15% | chunking |
| 4 | Generació d'embeddings via API batch | embedding |
| 5 | Upsert de vectors + metadades | indexed |
| Error | Qualsevol pas falla | failed + error_message |

### 7.5 Cerca documental (search_entity_knowledge)

1. La Tool rep query, entity_id i category opcional.
2. Es genera l'embedding de la consulta.
3. Cerca vectorial a document_chunks per entity_id (pgvector).
4. Filtra guide_documents.status = indexed.
5. Retorna top-K fragments.

```json
{
  "query": "horaris del museu",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 3,
  "results": [
    {
      "source": "Catàleg Museu de Bagà 2024",
      "page": 12,
      "summary": "Fragment de text rellevant...",
      "doc_id": "uuid",
      "entity_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ]
}
```

### 7.6 Model físic PostgreSQL

El DDL complet, taules entities, guide_documents i document_chunks, es manté a [postgre_schema.md](../postgre_schema.md) i [schema-agent-postgres.sql](../schema-agent-postgres.sql).

Resum:

- **entities** — una fila per client/àmbit (entity_type, name, slug, config, is_active).
- **guide_documents** — un PDF per fila; FK entity_id.
- **document_chunks** — fragments + embedding; entity_id denormalitzat per filtre RAG.

No duplicar l'esquema aquí; actualitzar postgre_schema.md en canvis de model.

---

## 8. Persistència de dades

### 8.1 MySQL femturisme

| Aspecte | Detall |
|---------|--------|
| Rol | Font de veritat del catàleg web. |
| Accés agent | Usuari agent_read, permís SELECT només. |
| Esquema | docs/schema.sql, DDL sense dades. |
| Canvis v1 | Cap esquema nou a MySQL. |
| Consultes | SQL fixa per operació; mapatge a JSON documentat a sql-mapeo.md. |

### 8.2 PostgreSQL agent

| Aspecte | Detall |
|---------|--------|
| Rol | Entitats, metadades documentals, chunks i vectors. |
| Esquema | docs/postgre_schema.md, docs/schema-agent-postgres.sql. |
| Accés | Usuari agent_app read/write. |
| Extensió | pgvector. |
| Hosting | Extern gestionat recomanat: Supabase, Neon, RDS o equivalent. |
| Escriptors | Només servei Python. |
| Separació | PostgreSQL no toca el catàleg web; MySQL no guarda vectors ni PDFs. |

### 8.3 Preguntes obertes de schema MySQL

Font: [schema.sql](../schema.sql), [sql-mapeo.md](../sql-mapeo.md) (validat 2026-07-20, issue #26).

| ID | Pregunta | Resposta / decisió dev | Estat | Owner |
|----|----------|------------------------|-------|-------|
| Q-01 | Nom exacte de la taula d'establiments i com es distingeix tipus dormir vs menjar | `establiment_general`; tipus via `establiment_tipus` → `generic_tipus_establiment` | Resolt dev | Client — relació `eg.tipus` |
| Q-02 | On viuen articles/notícies i quins camps retornar | `noticia_general` + `noticia_continguts` | Resolt dev | — |
| Q-03 | Taules de poblacions/on anar i relació amb comarques | `poble_general`, `poble_continguts`, `poble_comarques`, `generic_ubicacions` | Resolt dev | Client — visibilitat contracte |
| Q-04 | Taula i relacions d'experiències vs agenda | Agenda = `agenda_*`; experiències = `oferta_*` | Hipòtesi dev | Client — confirmació formal |
| Q-05 | URL canònica per tipus de fitxa | 6 patrons documentats a sql-mapeo §URLs; implementats a `mappers.py` | Parcial | Client — sign-off URLs articles/ofertes |
| Q-06 | Regles publicat, dates vigents i idioma per entitat | Documentades sql-mapeo §1.4–6.4; provades amb pytest | Parcial | Client — casos edge (periòdics, `es_oferta`) |
| Q-07 | Límits de JOINs legacy per a cada buscador | Màx. 6–8 JOINs; sense taules admin | Documentat | — |
| Q-08 | On emmagatzemar entity_id (UUID) a fitxes MySQL | No al schema actual | Obert | Fase 7 (DEV-700) |

### 8.4 Enllaç MySQL ↔ entitat (RF-15)

La relació portal → entitat es defineix només al costat MySQL/CMS (ADR-011):

- Una fitxa pot incloure entity_id (UUID) igual que entities.entity_id a PostgreSQL.
- El Repository MySQL inclou entity_id al JSON card quan existeix al schema.
- PostgreSQL no manté llista inversa de fitxes per entitat.
- Amb poques relacions inicials, mapatge manual al CMS és acceptable.

Flux en mode femturisme (Fase producte 2): catàleg → card amb entity_id → search_entity_knowledge.

---

## 9. API REST

### 9.1 POST /api/chat

Endpoint principal del xat. Implementació de referència: app/routes/api.py.

#### Request body

| Camp | Tipus | Obligatori | Descripció |
|------|-------|------------|------------|
| message | string | Sí | Text de l'usuari. |
| session_id | string | No | UUID sessió; si falta, el servidor en genera un. |
| page_context | object | No | Context de pàgina. |
| agent_context | object | No | Mode operatiu: mode (femturisme \| entitat), entity_id (obligatori si mode=entitat). |

#### Camps agent_context

| Camp | Tipus | Descripció |
|------|-------|------------|
| mode | string | femturisme (default) o entitat. |
| entity_id | UUID | Obligatori en mode entitat; null en mode femturisme. |

Response: text/event-stream (SSE). Errors HTTP: 400 si message és buit o absent; 500 en error intern controlat.

#### Events SSE

| type | Descripció | Camps addicionals |
|------|------------|-------------------|
| tool_call | Inici consulta Tool | tool, input |
| tool_result | Resultat consulta Tool | tool, result |
| text_chunk | Fragment de resposta | content |
| done | Fi del torn | full_text |
| error | Error | message |

#### Exemple SSE

```text
data: {"type":"tool_call","tool":"search_events","input":{"destination":"Empordà","date_from":"2026-06-28","date_to":"2026-06-29"}}

data: {"type":"tool_result","tool":"search_events","result":{"destination":"Empordà","date_from":"2026-06-28","date_to":"2026-06-29","total":"12","results":[{"title":"Fira medieval de Pals","url":"https://www.femturisme.cat/agenda/fira-medieval-pals","date":"28 de juny","description":"..."}]}}

data: {"type":"text_chunk","content":"Aquest cap de setmana a l'Empordà tens diverses opcions: "}

data: {"type":"done","full_text":"Aquest cap de setmana a l'Empordà tens diverses opcions: ..."}
```

### 9.2 POST /api/session/reset

Request:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Response:

```json
{
  "ok": true
}
```

Esborra l'historial en memòria per a la sessió indicada.

### 9.3 GET /health

Healthcheck per monitorització i desplegament. Resposta esperada: HTTP 200 amb cos indicant estat del servei. Recomanat incloure estat MySQL, PostgreSQL i disponibilitat bàsica del servei agent.

### 9.4 API d'administració d'entitats

| Mètode | Ruta | Descripció |
|--------|------|------------|
| POST | /admin/api/entities | Crear entitat (name, entity_type, slug, territory, config). |
| GET | /admin/api/entities | Llistat JSON d'entitats. |
| GET | /admin/api/entities/{entity_id} | Detall d'una entitat. |
| PUT | /admin/api/entities/{entity_id} | Actualitzar entitat. |
| DELETE | /admin/api/entities/{entity_id} | Eliminar entitat (CASCADE documents i chunks). |

### 9.5 API d'administració documental

| Mètode | Ruta | Descripció |
|--------|------|------------|
| POST | /admin/api/documents/upload | Pujada multipart: file, entity_id, title, category. |
| GET | /admin/api/documents | Llistat JSON (filtre opcional ?entity_id=). |
| GET | /admin/api/documents/{doc_id} | Detall document. |
| DELETE | /admin/api/documents/{doc_id} | Eliminació document + chunks + vectors + fitxer disc. |
| POST | /admin/api/documents/{doc_id}/reindex | Reexecutar pipeline. |
| POST | /admin/api/documents/{doc_id}/smoke-test | Prova de cerca amb query. |

La UI d'administració és al backend de femturisme; aquestes rutes són el contracte amb el servei agent. UI Python /admin/guides només com a prototip consumint la mateixa API.

### 9.6 Formulari de pujada de document

| Camp | Tipus | Obligatori |
|------|-------|------------|
| file | file PDF | Sí |
| entity_id | UUID | Sí |
| title | string | Sí |
| category | string | No |

Resposta exitosa: HTTP 201 amb doc_id i estat inicial pending.

---

## 10. Configuració

### 10.1 Entorns

| Entorn | MySQL | PostgreSQL | Servei Python | Widget |
|--------|-------|------------|---------------|--------|
| Staging | BD staging o read-only replica | Instància staging | Docker staging | femturisme staging |
| Producció | MySQL prod read-only | Instància prod | Docker prod | femturisme.cat |

No indexar PDFs de prova a producció.

### 10.2 Variables .env principals

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

### 10.3 Variables addicionals recomanades

- LOG_LEVEL
- RATE_LIMIT_PER_IP
- AGENT_TIMEOUT_SECONDS
- MYSQL_CONNECT_TIMEOUT
- POSTGRES_CONNECT_TIMEOUT
- ADMIN_API_TOKEN
- ALLOWED_ADMIN_IPS
- DOCUMENT_STORAGE_PATH

---

## 11. Desplegament

### 11.1 Docker

```yaml
services:
  agent:
    build: .
    ports:
      - "5000:5000"
    env_file: .env
    volumes:
      - ./data/guides:/app/data/guides

# PostgreSQL: NO al Docker de producció. URL externa al .env.
```

Dev local opcional: contenidor PostgreSQL amb imatge pgvector/pgvector.

### 11.2 Checklist desplegament

- Configurar .env de l'entorn.
- Construir imatge Docker.
- Verificar connexió MySQL amb usuari read-only.
- Verificar connexió PostgreSQL + pgvector.
- Arrencar servei Python.
- Comprovar GET /health.
- Configurar reverse proxy des de femturisme.cat.
- Fer smoke test amb POST /api/chat.

---

## 12. Seguretat

| Mesura | Detall |
|--------|--------|
| MySQL read-only | Usuari sense INSERT/UPDATE/DELETE. |
| SQL parametritzada | Consultes fixes al codi; no SQL generada per IA. |
| Allowlist implícita | Només Tools autoritzades. Sense accés SQL arbitrari. |
| Rate limiting | Límit de peticions a /api/chat per IP/sessió. |
| Secrets | Claus API a .env, mai al repositori. |
| Admin | Panell no públic; VPN/IP allowlist, Basic/token/SSO a decidir. |
| XSS | Escapar HTML al client; Markdown amb enllaços controlats. |
| PDFs | No indexables públicament; accés només intern. |

### 12.1 Seguretat del panell documental

- Accés per VPN o IP allowlist.
- Autenticació HTTP Basic, token o SSO intern.
- robots.txt i cap enllaç des del web públic.
- Validació de tipus i mida de fitxer.
- Eliminar vectors i metadades quan s'elimini un document.

---

## 13. Observabilitat i operació

### 13.1 Logging mínim

| Esdeveniment | Camps |
|--------------|-------|
| Request xat | session_id, durada total, idioma, operational_mode, entity_id |
| Consulta catàleg | nom operació, paràmetres, latència SQL, fila count |
| Consulta coneixement entitat | entity_id, latència vector, topK |
| Ingest PDF | doc_id, entity_id, pas, durada, error |
| Error | stack trace intern, session_id o doc_id, codi d'error |

### 13.2 Backups

| Recurs | Freqüència / criteri |
|--------|----------------------|
| PostgreSQL agent | Automàtic diari mitjançant proveïdor. |
| data/guides/ | Incloure en backup del servidor agent. |
| .env | No versionar; custodiar en sistema segur. |

### 13.3 Runbooks breus

| Incidència | Acció |
|------------|-------|
| PDF failed | Llegir error_message al panell, reindexar, contactar dev si persisteix. |
| MySQL inaccessible | Verificar xarxa/credencials; xat mostra error amigable. |
| Query lenta | EXPLAIN a staging; revisar índexs; confirmar LIMIT. |
| Embedding API down | Documents queden failed; reintentar quan servei recuperi. |
| LLM down | Retornar missatge temporal i registrar error. |
| PostgreSQL down | Desactivar consultes documentals i mantenir catàleg si és possible. |

---

## 14. Pla de proves

### 14.1 Tests SQL automatitzats

| Test | Paràmetres | Assert |
|------|------------|--------|
| SQL-01 | destination=Girona, type=hotel | >=0 files establiments, URL vàlida |
| SQL-02 | destination=Pals, type=restaurant | >=0 files menjar |
| SQL-03 | topic=Parc Natural Cadí | >=0 articles |
| SQL-04 | destination=Besalú | >=0 poblacions/on anar |
| SQL-05 | destination=Empordà, dates cap setmana | files agenda dins interval |
| SQL-06 | destination=Olvan | >=0 experiències |
| SQL-07 | destination=Empordà, type=A peu | >=1 ruta |

### 14.2 Tests API

| Test | Descripció | Assert |
|------|------------|--------|
| API-01 | POST /api/chat missatge buit | 400 |
| API-02 | Pregunta simple | SSE conté done |
| API-03 | Pregunta catàleg | seqüència tool_call + tool_result + text_chunk |
| API-04 | POST /api/session/reset | historial buit / ok true |

### 14.3 Tests integració/UAT

| Lot | N | Descripció |
|-----|---|------------|
| Catàleg | 12 | 2 proves per domini de catàleg |
| Guies/Documents | 10 | Entitats amb document indexat (search_entity_knowledge) |
| Mixtes | 10 | Catàleg + coneixement entitat (mateix entity_id, Fase producte 2) |
| Mode entitat | 8 | Agent només consulta fonts de l'entity_id indicat; sense fuites de catàleg |
| Total | ~30 | Routing correcte >=80% |

### 14.4 Tests admin entitats i documents

- CRUD entitat -> entity_id estable.
- Pujada document per entity_id -> indexed.
- Reindexar després de failed.
- Smoke-test amb entity_id retorna chunks.
- Eliminar document elimina chunks/vectors.
- Eliminar entitat elimina documents (CASCADE).
- Document failed no apareix en search_entity_knowledge.
- Mode entitat: POST /api/chat amb agent_context.mode=entitat rebutja accés a catàleg aliè.

### 14.5 Tests PHP

- Globus visible a home i pàgines interiors.
- Proxy sense CORS.
- Mobile Safari / Chrome Android.
- page_context correcte segons URL.

---

## 15. Pla d'implementació

### 15.0 Correspondència fases producte (requeriments.md) ↔ tècniques

| Fase producte | Abast | Fases tècniques |
|---------------|-------|-----------------|
| Fase producte 1 | Assistent femturisme; catàleg MySQL; RAG general; preguntes coneixement | 15.1–15.4 + 15.5 (sense mode entitat ni entity_id MySQL) |
| Fase producte 2 | Gestor entitats; assistent entitat; entity_id al portal; integració | 15.5 ampliada + 15.7 mode entitat + Q-08 |

### 15.1 Fase tècnica 1 - Servei Python al servidor

- Empaquetat Docker / requirements.txt.
- Desplegament staging.
- Configurar AGENT_*, MYSQL_*, POSTGRES_*, VECTOR_*.
- GET /health.
- POST /api/chat i POST /api/session/reset.
- Static files widget/admin si cal.
- Prova connexió MySQL.
- Prova connexió PostgreSQL.
- Smoke test agent.

### 15.2 Fase tècnica 2 - Exploració MySQL i disseny de queries

- Exportar docs/schema.sql sense dades.
- Resoldre Q-01 a Q-08.
- Documentar SQL a sql-mapeo.md.
- Validar URL canòniques.
- Definir regles de publicació, idioma i vigència.

### 15.3 Fase tècnica 3 - Tools de catàleg amb MySQL

- No implementar totes les Tools a la vegada.
- Començar per una Tool completa, recomanat search_experiences.
- Afegir Repository, Tool, schema de paràmetres i test.
- Repetir patró per la resta de Tools.
- Eliminar dependència de scraping quan el MySQL estigui complet.

Exemple patró de test:

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

### 15.4 Fase tècnica 4 - Integració web

- Widget i panell femturisme.cat.
- Reverse proxy.
- SSE render.
- page_context i agent_context (mode femturisme per defecte).
- Proves responsive.

### 15.5 Fase tècnica 5 - Base de coneixement d'entitats

- Aplicar schema-agent-postgres.sql (entities, guide_documents, document_chunks).
- API CRUD /admin/api/entities.
- API documents upload/list/detail/reindex/delete/smoke-test per entity_id.
- Pipeline d'extracció, chunking, embeddings i indexació.
- Tool search_entity_knowledge.
- Gestor entitats + documental al backend femturisme (UI).
- UAT amb entitats de prova i documents indexats.

### 15.6 Fase tècnica 6 - Integració entitats (Fase producte 2)

- Camp entity_id a fitxes MySQL (Q-08) i card JSON.
- Flux condicional catàleg → search_entity_knowledge (§5.6).
- Widget/xat propi per entitat amb agent_context.mode=entitat.
- Filtratge estricte de Tools en mode entitat.
- UAT mode entitat + mixtes catàleg/RAG.

### 15.7 Què NO s'ha de fer

| Error comú | Per què |
|------------|---------|
| Canviar noms de Tool sense actualitzar schema/prompt/tests | Trenca routing i proves. |
| Concatenar strings a SQL | Risc SQL injection. |
| Exposar SQL o taules al LLM | Fora d'arquitectura. |
| Fer text-to-SQL en producció | Decisió v1: no permès. |
| Escriure a MySQL | Usuari agent_read és SELECT only. |
| Mantenir scraper.py després del refactor | Codi mort i confusió. |

---

## 16. Decisions pendents i annexos

### 16.1 Decisions pendents

| ID | Tema | Opcions / comentari |
|----|------|---------------------|
| P-01 | Comunicació PHP-Python | HTTP intern, Docker network, host dedicat; definir autenticació i timeout. |
| P-02 | Hosting Python | Mateixa màquina que PHP vs servidor dedicat. |
| P-03 | Model LLM producció | Anthropic actual; mantenir configuració per proveïdor alternatiu. |
| P-04 | Persistència historial multi-instància | Memòria local v1; Redis/PostgreSQL si escala horitzontal. |
| P-05 | Vector store alternatiu | pgvector v1; Qdrant possible futur. |
| P-06 | Admin UI final | Backend femturisme com a UI principal; API Python com a servei. |

### 16.2 Annex A - Comparació text-to-SQL vs Tools parametritzades

Arquitectura adoptada: usuari en llenguatge natural -> LLM tria Tool + paràmetres -> Python executa SQL fixa -> JSON normalitzat -> LLM respon.

No s'utilitza execute_sql genèric perquè la complexitat no desapareix: es desplaça a seguretat, control de permisos, validació, rendiment, explicabilitat i proves. En un schema legacy amb relacions críptiques, el risc d'errors és alt encara que l'usuari MySQL sigui read-only.

| Aspecte | Tools parametritzades | Text-to-SQL |
|---------|----------------------|-------------|
| Seguretat | Consultes fixes, validables. | Cal sandbox, parser, allowlist i límits estrictes. |
| Rendiment | LIMIT i JOINs coneguts. | Risc de consultes lentes o cares. |
| Qualitat | JSON homogeni per al model. | Resultats variables segons SQL generada. |
| Manteniment | Un Repository per domini. | Cal explicar schema i relacions al model. |
| Testing | Tests previsibles per Tool. | Tests més difícils per variabilitat de SQL. |

### 16.3 Annex B - Referències internes

- requeriments.md - Presa de requeriments, RF-13/14/15, fases producte.
- funcional.md - Context operatiu, base de coneixement d'entitats.
- dominio-femturisme-ca.md - Model de negoci i definició dels dominis.
- postgre_schema.md - Model físic PostgreSQL (entitats + RAG).
- schema-agent-postgres.sql - DDL executable.
- sql-mapeo.md - SQL per Tool i mapping MySQL.
- plan-integracion-ca.md - Pla per fases.
- agente.md - Bucle agent i proveïdors LLM.
- fase-3-tools-mysql-ca.md - Guia implementació Repositories.
