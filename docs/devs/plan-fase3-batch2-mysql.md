# Pla: Fase 3 batch 2 — 6 buscadors MySQL complets

Completar el catàleg MySQL: **articles**, **routes**, **experiences** (encara scraping o absents), tancar **registry + scraper**, actualitzar **prompt**, i **tests integració batch 2**.

**Prerequisit tancat:** batch fase3-prep ([#5](https://github.com/3urega/femturisme/issues/5)…[#11](https://github.com/3urega/femturisme/issues/11)) — 3 buscadors MySQL + Railway amb dades reals.

**Estat:** publicat a GitHub ([#12](https://github.com/3urega/femturisme/issues/12)…[#17](https://github.com/3urega/femturisme/issues/17)) · Manifest: [manifest.fase3-batch2.json](../issues/manifest.fase3-batch2.json)

---

## Objectiu

| Què | Per què |
|-----|---------|
| `ArticlesRepository` + `search_articles` | DEV-203, DEV-303 — 6è domini de catàleg |
| `RoutesRepository` + tool MySQL | DEV-207, DEV-306 — eliminar scraping rutes |
| `ExperiencesRepository` + tool MySQL | DEV-206, DEV-301 — eliminar scraping ofertes |
| Registry 6 MySQL + retirar scraper | DEV-307, DEV-308 complets |
| Prompt amb articles disponible | DEV-310 — sense «pendent» |
| Tests SQL-03/06/07 | Validació Railway (com #11) |

**Fora d'abast:** widget PHP (Fase 4), RAG PostgreSQL, `search_local_knowledge` real, DEV-309 límits operatius (issue futura).

---

## Estat actual (post #12)

| Domini | Tool | Estat |
|--------|------|-------|
| Establiments | `search_establishments` | MySQL |
| On anar | `search_destinations` | MySQL |
| Agenda | `search_events` | MySQL |
| Articles | `search_articles` | MySQL *(#12, 2026-07-13)* |
| Rutes | `search_routes` | Scraping |
| Experiències | `search_experiences` | Scraping |

---

## Ordre d'implementació

```text
1. articles-repository-mysql      → DEV-203, DEV-303
2. routes-repository-mysql        → DEV-207, DEV-306
3. experiences-repository-mysql → DEV-206, DEV-301
4. registry-scraper-final       → DEV-307, DEV-308
5. system-prompt-articles       → DEV-310 (actualització)
6. integration-tests-batch2     → SQL-03/06/07 + repos
```

**Nota:** aplicar patrons strict mode de batch 1 (`ONLY_FULL_GROUP_BY`, dates zero-date) a SQL nou abans dels tests.

---

## GitHub issues

| Ordre | GitHub | Slug | Títol | Checklist |
|-------|--------|------|-------|-----------|
| 1 | [#12](https://github.com/3urega/femturisme/issues/12) ✅ | `articles-repository-mysql.md` | Fase 3 batch 2: ArticlesRepository + search_articles | DEV-203, DEV-303 |
| 2 | [#13](https://github.com/3urega/femturisme/issues/13) | `routes-repository-mysql.md` | Fase 3 batch 2: RoutesRepository + search_routes MySQL | DEV-207, DEV-306 |
| 3 | [#14](https://github.com/3urega/femturisme/issues/14) | `experiences-repository-mysql.md` | Fase 3 batch 2: ExperiencesRepository + search_experiences MySQL | DEV-206, DEV-301 |
| 4 | [#15](https://github.com/3urega/femturisme/issues/15) | `registry-scraper-final.md` | Fase 3 batch 2: Registry 6 MySQL i retirar scraper | DEV-307, DEV-308 |
| 5 | [#16](https://github.com/3urega/femturisme/issues/16) | `system-prompt-articles.md` | Fase 3 batch 2: System prompt amb search_articles | DEV-310 |
| 6 | [#17](https://github.com/3urega/femturisme/issues/17) | `integration-tests-mysql-batch2.md` | Fase 3 batch 2: Tests integració MySQL batch 2 | DEV-203, DEV-206, DEV-207 |

Manifest: [manifest.fase3-batch2.json](../issues/manifest.fase3-batch2.json)

---

## Verificació global (post-batch)

```powershell
python -m pytest -v
python -m pytest -m integration -v
python scripts/test_sql_queries.py --ping
rg "from \.scraper" app/services/tools/
```

---

## Referències

- [sql-mapeo.md](../sql-mapeo.md) §2, §6, §7
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md)
- [plan-fase3-prep-sense-mysql.md](plan-fase3-prep-sense-mysql.md)
- [checklist-entrega.md](checklist-entrega.md)
