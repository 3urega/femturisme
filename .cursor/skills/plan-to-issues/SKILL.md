---
name: plan-to-issues
description: >-
  Convert an implementation plan (.md roadmap or domain doc) into GitHub issue draft
  files under docs/issues plus a JSON manifest. Use before publish-github-issues when
  the user has a plan to implement, wants to generate issue bodies from a document,
  or says plan-to-issues, roadmap to issues, or crear issues en docs.
---

# Plan to Issues (docs first)

Repository: `3urega/femturisme`

**This is step 1** of the issue workflow. **Step 2** is [publish-github-issues](../publish-github-issues/SKILL.md) (upload to GitHub). **Step 3** lifecycle: [kanban-board](../kanban-board/SKILL.md) (implement + close + cleanup docs).

```text
Plan .md  →  [plan-to-issues]  →  docs/issues/*.md + manifest.json
                                        ↓
                              [publish-github-issues]  →  GitHub issues
                                        ↓
                              [kanban-board] implement → close → delete docs drafts
```

---

## When to use

- User has a roadmap or plan in `docs/fase-3-tools-mysql-ca.md`, `docs/plan-integracion-ca.md`, `docs/client/tecnic.md`, `docs/issues/*-draft.md`, or a Cursor plan.
- User asks: *genera las issues en docs*, *convierte el roadmap en issues*, *prepara el kanban*, *partir Fase 3 en issues*.
- **Do not** call `gh issue create` in this skill — only write files under `docs/issues/`.

---

## Input

One primary document, e.g.:

- `docs/fase-3-tools-mysql-ca.md`
- `docs/plan-integracion-ca.md`
- `docs/client/tecnic.md` (§15 pla d'implementació)
- `docs/issues/experiences-mysql-draft.md`
- Any `.md` with phases, vertical slices, acceptance criteria

Read **[AGENTS.md](../../../AGENTS.md)** and linked docs for context:

- [docs/arquitectura/index.md](../../../docs/arquitectura/index.md) — capes objectiu
- [docs/client/dominio-femturisme-ca.md](../../../docs/client/dominio-femturisme-ca.md) — 6 buscadors, regles de negoci

---

## Output (required)

1. **One body file per issue** in `docs/issues/`:

   Naming (before GitHub numbers exist): `{short-slug}.md`  
   Example: `experiences-repository-mysql.md`, `widget-sse-proxy.md`

   After publish, filenames may be renamed to `{githubNumber}-{slug}.md` (optional; publish skill).

2. **Manifest** `docs/issues/manifest.<batch-name>.json`:

```json
{
  "repo": "3urega/femturisme",
  "sourceDoc": "docs/fase-3-tools-mysql-ca.md",
  "defaultLabels": ["enhancement"],
  "issues": [
    {
      "title": "Fase 3: ExperiencesRepository + search_experiences MySQL",
      "bodyFile": "docs/issues/experiences-repository-mysql.md",
      "labels": ["fase-3", "mysql"]
    }
  ]
}
```

3. **Update source plan** — add section **GitHub issues (draft)** with table linking body files (not GitHub URLs until published).

---

## Issue body template

Each `docs/issues/<slug>.md` must include:

```markdown
## Objetivo
(one paragraph)

## Contexto
(dependencies, links to docs/client/, docs/arquitectura/)

## Alcance
| In | Fuera |
|----|-------|
| … | … |

## Criterios de aceptación
- [ ] …

## Capas / archivos principales
- `app/db/repositories/…`
- `app/services/tools/…`
- `tests/integration/sql/…`

## Issues relacionadas
- (other slugs in same batch)

## Referencias
- [source plan](../fase-3-tools-mysql-ca.md)
```

**Titles:** use `:` not em-dash `—` (PowerShell encoding).

**Verificación** (include in body or under Criterios):

```bash
pytest tests/integration/sql/test_experiences.py -v
curl -s http://127.0.0.1:5010/health
```

---

## Vertical slicing

Split the plan into **one GitHub issue per vertical slice** (same rules as [kanban-board](../kanban-board/SKILL.md)):

| Slice | Valor para el usuario | Capas |
|-------|----------------------|-------|
| VS1 | … | repository + tool + test |
| VS2 | … | … |

- Smallest deliverable per issue; cross layers when needed (repository + tool + pytest, not «toda la capa db/»).
- Mark **fuera de alcance** explicitly in each body (Alcance table).
- Order issues by dependency (manifest array order = implementation order).

Typical batch size: **3–7 issues**. Do not create one mega-issue for a whole roadmap.

---

## Project rules (embed in each draft when relevant)

| Rule | Detail |
|------|--------|
| No text-to-SQL | SQL only in repositories |
| Scraping = legacy | New issues → MySQL repositories, not `scraper.py` |
| RAG femturisme.cat | Fase 1: no RAG; Fase 2: only if `results[].entity_id` |
| Agenda ≠ experiencias | Separate domains / tools |
| New Python code | [patrones-y-convenciones.md](../../../docs/arquitectura/patrones-y-convenciones.md) |

Suggested labels:

| Label | Use |
|-------|-----|
| `fase-1` / `fase-2` | Product phase |
| `fase-3`, `mysql` | Catalog searchers |
| `rag`, `postgres` | Entities, pgvector |
| `agent`, `llm` | AgentService, modes |
| `php`, `widget` | femturisme.cat integration |
| `infra`, `ops` | Docker, deploy |
| `docs` | Documentation only |
| `legacy` | Remove scraping |

---

## Agent workflow

1. Read the source `.md` plan completely.
2. Read `AGENTS.md` + relevant architecture/domain docs.
3. Identify phases / slices; **one issue per vertical slice** (or per suggested GitHub issue row in the plan).
4. Write body files under `docs/issues/` (`{short-slug}.md`).
5. Write `manifest.<batch-name>.json` with `"repo": "3urega/femturisme"`.
6. Update source doc with **GitHub issues (draft)** table + link to manifest path.
7. Tell user: *Drafts ready in docs. Run `/publish-github-issues` with manifest … to upload.*

Present summary table:

| Slug | Title | Labels | Depends on |
|------|-------|--------|------------|

---

## Do not

- Publish to GitHub (that is `publish-github-issues`).
- Duplicate bodies already published (grep `docs/issues/` and `gh issue list --repo 3urega/femturisme` titles if unsure).
- Edit Cursor plan files in `.cursor/plans/` unless the user asks.
- Create horizontal layer issues («implement all repositories»).

---

## Related

- [publish-github-issues](../publish-github-issues/SKILL.md) — step 2
- [kanban-board](../kanban-board/SKILL.md) — implement, close, cleanup docs
- [docs/issues/README.md](../../../docs/issues/README.md) — workflow summary
