# Issue drafts — agent_femturisme

Borradors locals abans de publicar a GitHub (`3urega/femturisme`).

## Flux

```text
Plan .md  →  plan-to-issues  →  docs/issues/*.md + manifest.json
                                        ↓
                              publish-github-issues  →  GitHub
                                        ↓
                              kanban-board  →  implement → close → cleanup
```

Skills: `.cursor/skills/plan-to-issues`, `publish-github-issues`, `kanban-board`.

## Estructura

```text
docs/issues/
├── README.md
├── manifest.<batch>.json       # p.ex. manifest.fase3-mysql.json
├── experiences-repository-mysql.md
└── ...
```

**Naming:** `{short-slug}.md` abans de publicar; opcional `{githubNumber}-{slug}.md` després.

## Manifest

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

Després de publicar: afegir `"githubNumber": 42` i `"publishedAt": "YYYY-MM-DD"`.

## Plantilla de body

```markdown
## Objetivo

## Contexto

## Alcance
| In | Fuera |
|----|-------|

## Criterios de aceptación
- [ ] …

## Capas / archivos principales

## Issues relacionadas

## Referencias
```

## Pla font

Després de `plan-to-issues`, el document font ha d'incloure secció **GitHub issues (draft)** amb taula de slugs (sense URLs de GitHub fins publicar).

**Batch tancat:** [plan-fase6-pre-entrega.md](../devs/plan-fase6-pre-entrega.md) — **complet** ([#23](https://github.com/3urega/femturisme/issues/23)–[#26](https://github.com/3urega/femturisme/issues/26), 2026-07-20).

**Batch RAG:** [plan-fase5-rag-base.md](../devs/plan-fase5-rag-base.md) → [manifest.fase5-rag.json](manifest.fase5-rag.json) — **en curs** ([#27](https://github.com/3urega/femturisme/issues/27)–[#29](https://github.com/3urega/femturisme/issues/29), [#33](https://github.com/3urega/femturisme/issues/33) tancats, [#31](https://github.com/3urega/femturisme/issues/31)–[#32](https://github.com/3urega/femturisme/issues/32) obertes, 2026-07-20).

**Batch posposat:** [plan-fase4-php-widget.md](../devs/plan-fase4-php-widget.md) → [manifest.fase4-php.json](manifest.fase4-php.json) — **publicat** ([#18](https://github.com/3urega/femturisme/issues/18)…[#22](https://github.com/3urega/femturisme/issues/22), 2026-07-13). En espera accés PHP.

**Batch tancat:** [plan-fase3-batch2-mysql.md](../devs/plan-fase3-batch2-mysql.md) — **complet** ([#12](https://github.com/3urega/femturisme/issues/12)…[#17](https://github.com/3urega/femturisme/issues/17), 2026-07-13).

**Batch anterior:** [plan-fase3-prep-sense-mysql.md](../devs/plan-fase3-prep-sense-mysql.md) — **tancat** ([#5](https://github.com/3urega/femturisme/issues/5)…[#11](https://github.com/3urega/femturisme/issues/11)).

**Batch anterior:** [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md) → [manifest.fase1-base-local.json](manifest.fase1-base-local.json) — tancat ([#1](https://github.com/3urega/femturisme/issues/1)…[#4](https://github.com/3urega/femturisme/issues/4)).

## Neteja

Quan es tanca una issue, **kanban-board** elimina el draft, actualitza el manifest i marca el pla font com a implementat.
