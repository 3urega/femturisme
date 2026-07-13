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

**Batch actiu:** [plan-fase3-batch2-mysql.md](../devs/plan-fase3-batch2-mysql.md) → [manifest.fase3-batch2.json](manifest.fase3-batch2.json) — **publicat** ([#12](https://github.com/3urega/femturisme/issues/12)…[#17](https://github.com/3urega/femturisme/issues/17)).

Ordre: codi #12–#16 primer; **tests MySQL al final** ([#17](https://github.com/3urega/femturisme/issues/17)).

**Batch anterior:** [plan-fase3-prep-sense-mysql.md](../devs/plan-fase3-prep-sense-mysql.md) — **tancat** ([#5](https://github.com/3urega/femturisme/issues/5)…[#11](https://github.com/3urega/femturisme/issues/11)).

**Batch anterior:** [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md) → [manifest.fase1-base-local.json](manifest.fase1-base-local.json) — tancat ([#1](https://github.com/3urega/femturisme/issues/1)…[#4](https://github.com/3urega/femturisme/issues/4)).

## Neteja

Quan es tanca una issue, **kanban-board** elimina el draft, actualitza el manifest i marca el pla font com a implementat.
