# Estat actual vs arquitectura objectiu

Avaluació honesta del codi Python existent (març 2026) i mapa de migració.

---

## Resum executiu

| Dimensió | Avui (prototip) | Objectiu (v2.1) |
|----------|-----------------|-----------------|
| Capa routes | Adequada | Mantenir |
| Agent loop + SSE | Adequat | Mantenir + filtratge per mode |
| Providers LLM | Bo (Strategy) | Mantenir |
| Tools / registry | Bo patró, mala font de dades | 7 tools + repositories |
| Repositories / BD | **Inexistent** | MySQL + PostgreSQL |
| DDD | No | No cal — capes + repositories |
| SOLID | Parcial | Reforçar DIP i SRP a AgentService |
| Tests | Scripts `tmp/` | pytest + tests/sql |
| RAG | Stub dummy | PostgreSQL + pgvector |

**Verdict:** el nucli (agent + LLM + tool registry) segueix **bones pràctiques per a un prototip**. No segueix encara l'arquitectura objectiu de producció perquè **falta tota la capa de dades** i parteix de scraping legacy.

---

## Què està bé avui

### Application Factory Flask

`create_app()` a `app/__init__.py` — patró estàndard, testeable amb `app.test_client()`.

### Separació routes / services

`app/routes/api.py` delega en `AgentService`; no conté lògica de negoci.

### Tool registry

`app/services/tools/__init__.py` — contracte uniforme `SCHEMA` + `execute()`, centralitzat.

### Capa LLM (Strategy + Factory)

`app/services/llm_service.py`:

- `BaseLLMProvider` abstracte
- Implementacions intercanviables (dummy, anthropic, openai, gemini)
- `build_provider()` — **OCP** ben aplicat

### Bucle agent documentat

`app/services/agent_service.py` — flux ReAct clar, events SSE tipats (`tool_call`, `tool_result`, `text_chunk`, `done`).

---

## Deute tècnica i gaps

### 1. Capa de dades absent

```
app/db/                    ← NO EXISTEIX
tests/                     ← NO EXISTEIX
```

Totes les tools de catàleg criden `scraper.py` (HTML públic). Això contradiceix [tecnic.md](../client/tecnic.md) i [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md).

### 2. Tools legacy vs objectiu

| Codi actual | Objectiu |
|-------------|----------|
| `search_accommodations` | `search_establishments` |
| `search_experiences` (ofertes `/ofertes`) | Experiències promocionals MySQL |
| `search_local_knowledge` (dummy) | `search_entity_knowledge` + PostgreSQL |
| 4 tools scraping | 6 buscadors MySQL |
| — | `search_articles`, `search_destinations` |

### 3. SOLID — punts febles

| Principi | Problema | Fitxer |
|----------|----------|--------|
| **SRP** | AgentService barreja orquestració, historial, prompt, streaming | `agent_service.py` |
| **SRP** | Tools coneixen URLs i DOM HTML | `experiences.py`, `scraper.py` |
| **DIP** | `current_app.config` dins `AgentService.run()` | `agent_service.py:56` |
| **DIP** | Tools importen scraper concret, no abstracció | `tools/*.py` |

### 4. Acoblament i escalabilitat

```python
# agent_service.py — estat global
_history: dict[str, list[dict]] = {}
```

- No escala amb múltiples workers
- Sense TTL ni persistència
- Comentari al codi ja indica substituir per BD/Redis

### 5. Config incompleta

`app/config.py` només defineix LLM. Falten `MYSQL_*`, `POSTGRES_*`, rate limiting, paths de documents.

### 6. Sense tests automatitzats

Només scripts manuals a `tmp/`. Cap `pytest` a `requirements.txt`.

---

## DDD — cal implementar-lo?

**No com a DDD tàctic complet.** El domini de negoci està documentat als docs del client (6 buscadors, entitats, modes), però el codi no necessita:

- entitats de domini amb comportament ric,
- agregats, domain events,
- bounded contexts separats en microserveis.

**Sí cal:**

- **Repositories** com a frontera d'accés a dades per «domini de catàleg» i «domini documental»
- **Tools** com a anti-corruption layer cap al LLM
- **Mappers** per traduir el model legacy MySQL → JSON estable

Això és arquitectura en capes + Repository, no DDD estricte — i és l'adequat per aquest projecte.

---

## Mapa de migració

```text
Fase actual (prototip)
├── Mantenir: agent_service loop, llm_service, routes/api SSE
├── Mantenir: patró Tool (SCHEMA + execute + registry)
└── Substituir: scraper → repositories MySQL

Fase 3 (MySQL)
├── Crear app/db/connection.py, mappers.py
├── Crear 6 repositories
├── Refactor execute() de cada tool
├── Renombrar accommodations → establishments
├── Afegir articles, destinations
└── tests/integration/sql/

Fase 5 (PostgreSQL + RAG)
├── repositories/entities.py, documents.py
├── search_entity_knowledge
├── document_service (pipeline)
└── Admin API

Fase 2 producte (integració RAG femturisme)
├── entity_id a cards MySQL
├── Flux condicional post-catàleg
└── Filtratge Tools per mode a AgentService
```

Guia detallada: [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md).

---

## Refactors recomanats (prioritat)

| Prioritat | Acció |
|-----------|-------|
| P0 | Introduir `app/db/` + primer repository complet (p.ex. experiences) |
| P0 | Tests pytest amb fixture Flask |
| P1 | Externalitzar prompts a `app/prompts/` |
| P1 | `ToolPolicy` o mètode `_tools_for_mode(agent_context)` |
| P2 | Injectar LLM provider al constructor d'AgentService |
| P2 | Historial behind interface (InMemory → Redis) |
| P3 | Eliminar `scraper.py` quan MySQL estigui complet |

---

## Conclusió per a agents i desenvolupadors

**Codi nou:** seguir [capas-y-modulos.md](capas-y-modulos.md) i [patrones-y-convenciones.md](patrones-y-convenciones.md). No copiar el patró scraping excepte manteniment legacy explícit.

**Codi existent:** vàlid com a prototip demostrable; no és referència per a producció.
