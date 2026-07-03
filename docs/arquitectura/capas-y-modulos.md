# Capes i mòduls

Estructura de directoris i responsabilitats del servei Python (Flask).

---

## Vista per capes

```text
┌─────────────────────────────────────────────────────────┐
│  Presentació / Entrada HTTP                              │
│  app/routes/          Blueprints Flask, SSE, validació   │
│  app/static/          Widget JS (demo / reutilitzable)   │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Aplicació / Orquestració                                │
│  app/services/agent_service.py   Bucle LLM + historial   │
│  app/services/llm_service.py     Providers LLM           │
│  app/services/document_service.py (futur: pipeline RAG)  │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Casos d'ús exposats al LLM (Tools)                      │
│  app/services/tools/      SCHEMA + execute() per tool    │
│  app/services/tools/__init__.py  Registry ALL_TOOLS      │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Accés a dades                                           │
│  app/db/repositories/     SQL fixa, cerca vectorial      │
│  app/db/connection.py     Pools MySQL / PostgreSQL       │
│  app/db/mappers.py        row → card JSON                │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│  Infraestructura                                         │
│  app/config.py            Variables d'entorn             │
│  data/guides/             PDFs originals (disc)          │
└─────────────────────────────────────────────────────────┘
```

---

## Estructura de carpetes (objectiu)

```text
agent_femturisme/
├── main.py
├── app/
│   ├── __init__.py              # create_app(), blueprints
│   ├── config.py                # Config per entorn
│   ├── routes/
│   │   ├── api.py               # /api/chat, /api/session/reset, /health
│   │   ├── admin.py             # /admin/api/* (futur)
│   │   └── main.py              # Demo UI
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── llm_service.py
│   │   ├── document_service.py  # Pipeline indexació (futur)
│   │   └── tools/
│   │       ├── __init__.py      # Registry
│   │       ├── establishments.py
│   │       ├── articles.py
│   │       ├── destinations.py
│   │       ├── routes_tool.py
│   │       ├── events.py
│   │       ├── experiences.py
│   │       └── entity_knowledge.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── mappers.py
│   │   └── repositories/
│   │       ├── establishments.py
│   │       ├── articles.py
│   │       ├── destinations.py
│   │       ├── routes.py
│   │       ├── events.py
│   │       ├── experiences.py
│   │       ├── entities.py
│   │       └── documents.py
│   ├── prompts/                 # System prompts per mode (futur)
│   └── static/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
│       └── sql/                 # Tests per repository
├── data/guides/
└── docs/
```

---

## Responsabilitat per capa

| Capa | Fa | No fa |
|------|-----|-------|
| **routes/** | HTTP, validació entrada, SSE, codis d'estat | SQL, crides LLM directes, lògica de negoci |
| **services/** | Orquestració, historial, selecció de Tools per mode | Parsejar HTML, SQL inline |
| **tools/** | Validar paràmetres, cridar repository, retornar JSON | Generar text per l'usuari, accés BD directe |
| **repositories/** | Consultes parametritzades, LIMIT, mapatge fila→dict | Decidir quina tool usar, conèixer el LLM |
| **mappers.py** | Transformar files BD → card JSON comú | Lògica de cerca |

---

## Regles de dependència

Les fletxes només van **cap avall**:

```text
routes → services → tools → repositories → connection
```

**Prohibit:**

- `repositories/` importa de `services/` o `routes/`
- `tools/` importa de `scraper.py` en codi nou (legacy)
- SQL dins `agent_service.py` o dins `routes/`
- El LLM rep taules, connection strings o stack traces

---

## Configuració

Tot el secret i config d'entorn a `app/config.py` + `.env`:

| Prefix | Ús |
|--------|-----|
| `AGENT_*` | LLM, iteracions, timeouts |
| `MYSQL_*` | Catàleg read-only |
| `POSTGRES_*` | Entitats + RAG |
| `OPENAI_*` | Embeddings |

Les classes `Config` no han de obrir connexions; només exposar valors. Els pools viuen a `db/connection.py`.

---

## Modes operatius i Tools

El filtratge de quines Tools veu el LLM és responsabilitat de **`AgentService`** (o un mòdul `tool_policy.py` si creix):

| Mode | Tools exposades |
|------|-----------------|
| femturisme (Fase 1) | 6 buscadors MySQL |
| femturisme (Fase 2) | 6 buscadors + `search_entity_knowledge` només després de resultats amb `entity_id` |
| entitat | Només `search_entity_knowledge` |

Veure [funcional.md §7](../client/funcional.md) i [tecnic.md §4.9](../client/tecnic.md).

---

## On posar codi nou

| Feature | Fitxers |
|---------|---------|
| Nou buscador MySQL | `db/repositories/<domini>.py` + `services/tools/<domini>.py` + registre `__init__.py` |
| API admin entitats | `routes/admin.py` + `repositories/entities.py` |
| Pipeline PDF | `services/document_service.py` + `repositories/documents.py` |
| Prompt per mode | `prompts/femturisme.py`, `prompts/entitat.py` |
| Test integració SQL | `tests/integration/sql/test_<domini>.py` |
