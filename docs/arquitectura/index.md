# Arquitectura del servei agent

Guia **obligatòria** per implementar codi nou al projecte `agent_femturisme`. Qualsevol feature (Tools, repositories, APIs, RAG, admin) ha d'encaixar en aquest model.

**Abans de codificar:** domini → [requeriments.md](../client/requeriments.md) / [funcional.md](../client/funcional.md) → [tecnic.md](../client/tecnic.md) → **aquesta carpeta**.

---

## Documents d'arquitectura

| Document | Què defineix |
|----------|--------------|
| **[Capes i mòduls](capas-y-modulos.md)** | Estructura de carpetes, responsabilitat per capa, flux de dades |
| **[Patrons i convencions](patrones-y-convenciones.md)** | Repository, Tool, contractes JSON, SOLID aplicat al projecte, regles de codi |
| **[Estat actual vs objectiu](estado-actual-vs-objetivo.md)** | Què fa el prototip avui, deute tècnica, mapa de migració |

---

## Principis no negociables

1. **Tools parametritzades** — el LLM no executa SQL lliure ni accedeix a BD directament.
2. **MySQL read-only** — usuari `agent_read`, consultes fixes als repositories.
3. **Separació catàleg / documental** — MySQL (portal) vs PostgreSQL (entitats + RAG).
4. **Mode operatiu** — filtratge de Tools segons `agent_context.mode` (femturisme / entitat).
5. **RAG condicional** — en mode femturisme, RAG només si `results[].entity_id` (Fase 2); Fase 1 sense RAG al xat públic.
6. **JSON normalitzat** — sortida de Tools amb contracte comú (cards + wrapper); veure [tecnic.md §6.13](../client/tecnic.md).

---

## Flux d'una petició (objectiu)

```text
HTTP POST /api/chat
    → routes/api.py          (validació, SSE)
    → AgentService           (bucle LLM + historial)
    → execute_tool()         (registry)
    → Tool.execute()         (validació paràmetres)
    → Repository             (SQL fixa / vector search)
    → MySQL | PostgreSQL
    → JSON normalitzat
    → LLM → resposta usuari
```

---

## Què **no** és aquest projecte

- **No** és DDD estricte (sense agregats, domain events ni bounded contexts explícits).
- **No** és hexagonal pur (adaptadors sí, però sense ports formalment tipats a tot arreu).
- **Sí** és arquitectura **en capes pragmàtica**: routes → services → tools → repositories → BD, amb SOLID on aporta valor.

Veure [patrones-y-convenciones.md](patrones-y-convenciones.md) per al detall.

---

## Enllaços relacionats

- [agente.md](../agente.md) — bucle tool-use i SSE
- [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md) — guia implementació repositories
- [postgre_schema.md](../postgre_schema.md) — model PostgreSQL
- [sql-mapeo.md](../sql-mapeo.md) — SQL per buscador
- [AGENTS.md](../../AGENTS.md) — workflow per agents
