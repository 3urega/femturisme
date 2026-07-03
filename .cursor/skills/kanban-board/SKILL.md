---
name: kanban-board
description: >-
  Manage the kanban board for 3urega/femturisme: list, read, plan with
  layered architecture review (not literal issue copy), vertical slicing,
  implement, close GitHub issues, and clean up docs/issues drafts when closed.
  Use for /kanban-board or when closing an issue.
---

# Kanban Board

Repository: **`3urega/femturisme`**

All `gh` commands require `--repo 3urega/femturisme`.

**Issue lifecycle:** [plan-to-issues](../plan-to-issues/SKILL.md) → [publish-github-issues](../publish-github-issues/SKILL.md) → **kanban-board** (this skill).

---

## Commands

List open issues:

```bash
gh issue list --repo 3urega/femturisme
```

View a specific issue:

```bash
gh issue view <number> --repo 3urega/femturisme
```

Close an issue:

```bash
gh issue close <number> --repo 3urega/femturisme --comment "Done: <brief summary>"
```

---

## Behavior

### Without arguments

List all open issues and show a summary to the user.

### With an issue ID (e.g. `/kanban-board 42`)

**No traduzcas la issue a un plan mecánico.** Primero entiende el contexto y diseña la mejor solución; después presenta el plan (con mejoras propuestas si las hay).

---

### Fase 1 — Leer la issue (punto de partida, no verdad absoluta)

```bash
gh issue view <id> --repo 3urega/femturisme
```

Extrae: objetivo, criterios de aceptación, dependencias, verificación mencionada y **fuera de alcance** explícito.

---

### Fase 2 — Contexto y arquitectura (obligatorio antes del plan)

Investiga **antes** de proponer slices. No basta con leer la issue.

1. **[AGENTS.md](../../../AGENTS.md)** — dominio, 6 buscadors, constraints, mapa de docs, legacy vs objectiu.

2. **Docs según tipo de issue** (solo lo relevante):

   | Tipo | Leer |
   |------|------|
   | Catálogo / MySQL | [dominio-femturisme-ca.md](../../../docs/client/dominio-femturisme-ca.md), [sql-mapeo.md](../../../docs/sql-mapeo.md), [fase-3-tools-mysql-ca.md](../../../docs/fase-3-tools-mysql-ca.md) |
   | Arquitectura / código Python | [docs/arquitectura/](../../../docs/arquitectura/index.md) → capas, patrones, estado actual |
   | API / agent / SSE | [tecnic.md](../../../docs/client/tecnic.md) §5–9, [agente.md](../../../docs/agente.md) |
   | RAG / entidades / PostgreSQL | [postgre_schema.md](../../../docs/postgre_schema.md), [funcional.md](../../../docs/client/funcional.md) §8.4, [requeriments.md](../../../docs/client/requeriments.md) Fase 2 |
   | Widget / PHP / proxy | [tecnic.md](../../../docs/client/tecnic.md) §4.7–4.8, [funcional.md](../../../docs/client/funcional.md) |
   | Producto / RF | [requeriments.md](../../../docs/client/requeriments.md), [funcional.md](../../../docs/client/funcional.md) |

3. **Código existente** — buscar patrones en el mismo ámbito:
   - `app/services/tools/` — contrato SCHEMA + execute
   - `app/services/agent_service.py`, `llm_service.py`
   - `app/db/repositories/` (si existe) — **objetivo**; no copiar `scraper.py` salvo mantenimiento legacy explícito

4. **Estado real vs issue** — ¿asume MySQL/RAG que aún no existen? ¿Propone scraping cuando toca repository? ¿Respeta Fase 1 sin RAG en femturisme.cat?

---

### Fase 3 — Diseño (arquitectura en capas + mejoras)

Con el contexto cargado, **diseña** la implementación (no copies la issue):

- **Capa correcta:** routes → services → tools → repositories → BD ([capas-y-modulos.md](../../../docs/arquitectura/capas-y-modulos.md)).
- **Tool + Repository** — SQL solo en repository; JSON normalizado en tool ([patrones-y-convenciones.md](../../../docs/arquitectura/patrones-y-convenciones.md)).
- **Modo operatiu** — femturisme vs entitat; RAG condicional solo con `entity_id` en resultados (Fase 2).
- **Dominio de negocio** — agenda ≠ experiencias; establishments unifica dormir+menjar.
- **Consistencia** — type hints, pytest, no secrets en repo.

**Mejoras propuestas** (cuando aporten valor):

| Tipo | Ejemplo | Acción |
|------|---------|--------|
| Refactor colindante | Extraer mapper duplicado | Incluir si es barato |
| Deuda legacy | Issue pide tocar scraping | Proponer migración MySQL según fase |
| Ajuste API JSON | Campo `entity_id` en card | Proponer si encaja en RF-15 |
| Desviación de la issue | Renombrar tool, ampliar scope | **Preguntar al usuario** |
| Fuera de alcance | Feature no pedida | Marcar «no incluir» |

Si hay desvíos, sección **Propuestas / desvíos** con: qué cambia, por qué, impacto.

---

### Fase 4 — Plan de implementación (entregar al usuario)

Presentar en este orden:

1. **Resumen** — qué pide la issue y qué se construirá realmente.
2. **Contexto encontrado** — archivos, docs, patrones (bullets).
3. **Propuestas / desvíos** (si hay).
4. **Slices verticales** (VS1, VS2, …) — ver abajo.
5. **Riesgos y mitigaciones** (schema MySQL TBD, scraping frágil, multi-worker historial…).
6. **Checklist de verificación** — pytest, smoke manual, CA aplicables.

**Espera confirmación** si hay desvíos materiales. Si el usuario dice «implementa», ejecuta el plan acordado.

---

### Fase 5 — Implementación

Completar y verificar **un slice antes del siguiente**, salvo que el usuario pida paralelizar.

Reglas de código:

- Seguir [docs/arquitectura/patrones-y-convenciones.md](../../../docs/arquitectura/patrones-y-convenciones.md)
- Documentar SQL nueva en `docs/sql-mapeo.md` antes o junto al repository
- Registrar tools en `app/services/tools/__init__.py`
- No commit unless user asks

**Verificación típica:**

```bash
pytest tests/integration/sql/ -v -m integration
python main.py   # smoke /health, POST /api/chat
```

---

### After completing work — close issue

Close only when **all slices** done and verified:

```bash
gh issue close <number> --repo 3urega/femturisme --comment "Done: <brief summary>"
```

Then **clean up docs** (mandatory):

#### 0. Update delivery checklist

Mark corresponding items in [docs/devs/checklist-entrega.md](../../../docs/devs/checklist-entrega.md) as `- [x]` when **Detect** criteria are met. Update progress counter at top.

#### 1. Find local drafts

```bash
# Body file with issue number prefix
docs/issues/<number>-*.md

# Manifest entries
grep -l "githubNumber.*<number>" docs/issues/manifest.*.json
grep -l "\"bodyFile\"" docs/issues/manifest.*.json

# Match by title
gh issue view <number> --repo 3urega/femturisme --json title
```

#### 2. Delete issue draft files

- **Delete** body file(s) in `docs/issues/` for this issue.
- **Remove** matching entry from every `docs/issues/manifest.*.json`.
- If manifest `issues[]` is empty, **delete** the manifest file.

**Do not delete** domain/roadmap docs (`docs/client/`, `docs/plan-integracion-ca.md`) — only update status.

#### 3. Update source / roadmap docs

In manifest `sourceDoc` or issue **Referencias**:

- Mark phase/item as **Implemented** with GitHub `#<number>` and date.
- Shrink draft tables that only listed unpublished work.

#### 4. Confirm to user

Report: issue URL + files deleted/updated under `docs/`.

---

## Vertical slicing

Partir el trabajo en **slices verticales** (valor de punta a punta). No planificar por capas horizontales («primero toda la API, luego repositories»).

### Qué es un slice vertical

Cada slice (VS1, VS2, …):

1. **Aporta valor verificable** (test, endpoint, tool funcional).
2. **Cruza capas** mínimas: repository + tool + test (o route + service si toca agent).
3. **Es mergeable** por sí solo.
4. **Es lo más pequeño** que cumple un criterio de aceptación.

### Plan template

| Slice | Valor / CA que cierra | Capas / archivos |
|-------|----------------------|------------------|
| VS1 | … | … |
| VS2 | … | … |

### Ejemplo — Fase 3 MySQL experiences

- **VS1:** `db/connection.py` + `ExperiencesRepository.search()` + test SQL vacío/con datos
- **VS2:** Refactor `experiences.py` tool → repo; eliminar import scraper
- **VS3:** Documentar SQL en `sql-mapeo.md`; UAT pregunta real al agent

### Reglas

- Investigar antes de planificar (Fases 2–3 obligatorias).
- Orden: menor → mayor dependencia; primero «tracer bullet».
- Marcar **fuera de alcance** del issue.
- Issue trivial → un solo slice (pero revisar contexto si toca modes/RAG/MySQL).
- Respetar `AGENTS.md` y fases producte (Fase 1 = sin RAG en femturisme.cat).

---

## Related

- [plan-to-issues](../plan-to-issues/SKILL.md)
- [publish-github-issues](../publish-github-issues/SKILL.md)
- [docs/issues/README.md](../../../docs/issues/README.md)
- [docs/arquitectura/estado-actual-vs-objetivo.md](../../../docs/arquitectura/estado-actual-vs-objetivo.md)
