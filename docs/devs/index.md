# Índex per a developers — agent_femturisme

Guia d'entrada per implementar i lliurar l'assistent de **femturisme.cat** des de zero fins a producció.

**Font de veritat funcional:** [docs/client/](../client/)  
**Font de veritat tècnica:** [tecnic.md](../client/tecnic.md) + [arquitectura/](../arquitectura/)  
**Checklist executable:** **[checklist-entrega.md](checklist-entrega.md)** ← document principal

---

## Ordre de lectura (abans de codificar)

| Ordre | Document | Per què |
|-------|----------|---------|
| 1 | [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) | 6 buscadors + entitats; agenda ≠ experiències |
| 2 | [requeriments.md](../client/requeriments.md) | RF, CA, Fases 1/2 |
| 3 | [funcional.md](../client/funcional.md) | Comportament agent, modes operatius |
| 4 | [tecnic.md](../client/tecnic.md) | API, tools, desplegament |
| 5 | [arquitectura/index.md](../arquitectura/index.md) | Capes, patrons, codi nou |
| 6 | [checklist-entrega.md](checklist-entrega.md) | Passos amb checkboxes |
| 7 | [testing.md](testing.md) | pytest, API-01…04, SQL-01…07 |

---

## Mapa de fases

```text
Fase 0   Documentació + acords          (parcialment feta)
   ↓
Fase A   Pre-requisits client           (MySQL schema, accés, staging)
   ↓
Fase 1   Servei Python base             (Docker, /api/chat, /health)
   ↓
Fase 2   Exploració MySQL + sql-mapeo   (Q-01…Q-08)
   ↓
Fase 3   6 buscadors MySQL              (repositories + tools; sense scraping)
   ↓
Fase 4   Integració femturisme.cat      (PHP proxy, widget, SSE)
   ↓
Fase 5   Infra RAG / PostgreSQL         (admin, pipeline; xat públic F1 sense RAG)
   ↓
Fase 6   Entrega Fase producte 1        (UAT, CA, staging sign-off)
   ↓
Fase 7   Fase producte 2                (entitats, mode entitat, entity_id, RAG condicional)
   ↓
Fase 8   Ops + producció                (seguretat, backups, monitorització)
   ↓
Fase 9   Entrega final client
```

Correspondència detallada: [tecnic.md §15](../client/tecnic.md).

---

## Workflow issues GitHub

| Skill | Acció |
|-------|--------|
| `plan-to-issues` | Pla → drafts `docs/issues/` |
| `publish-github-issues` | Manifest → GitHub `3urega/femturisme` |
| `kanban-board` | Implementar → tancar issue → marcar checklist |

En tancar una issue, l'agent ha d'actualitzar **[checklist-entrega.md](checklist-entrega.md)** (checkboxes corresponents).

---

## Instruccions per a agents (auto-marcar checkboxes)

Quan completis feina verificable:

1. Obre [checklist-entrega.md](checklist-entrega.md).
2. Cerca l'ID (`DEV-xxx`) relacionat amb la feina.
3. Comprova el criteri **Detect** (fitxer existeix, test passa, endpoint respon…).
4. Canvia `- [ ]` per `- [x]` **només** si la evidència és clara.
5. Afegeix data opcional: `- [x] DEV-xxx … *(2026-07-03)*`

**No marcar** si només hi ha prototip parcial, TODO, o scraping quan tocava MySQL.

Actualitzar també el comptador de progrés al cap del checklist.

---

## Documents de suport per fase

| Fase | Docs clau |
|------|-----------|
| MySQL | [fase-2-tools-mysql-ca.md](../fase-2-tools-mysql-ca.md), [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md), [sql-mapeo.md](../sql-mapeo.md) |
| Agent / SSE | [agente.md](../agente.md) |
| Tests | [testing.md](testing.md) |
| PostgreSQL / RAG | [postgre_schema.md](../postgre_schema.md), [schema-agent-postgres.sql](../schema-agent-postgres.sql) |
| Roadmap | [plan-integracion-ca.md](../plan-integracion-ca.md) |
| Legacy (no perpetuar) | [scraping-y-respuestas.md](../scraping-y-respuestas.md) |

---

## Estat ràpid

Veure barra de progrés a [checklist-entrega.md](checklist-entrega.md) (s'actualitza en marcar items).
