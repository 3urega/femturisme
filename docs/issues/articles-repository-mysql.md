## Objetivo

Implementar el 6è buscador de catàleg: **`ArticlesRepository`** + tool **`search_articles`** sobre MySQL (`noticia_*`), amb mapper `article` i registre a `ALL_TOOLS` (DEV-203, DEV-303).

## Contexto

- Checklist: **DEV-203**, **DEV-303**
- Batch fase3-prep (#5–#11) va completar establishments, destinations, events; **articles** queda pendent al prompt i al registry.
- SQL borrador: [sql-mapeo.md](../sql-mapeo.md) §2 — cas prova **SQL-03** (Parc Natural Cadí).
- MySQL dev: Railway (còpia producció) — aplicar fixes strict mode (`GROUP BY`, dates) com batch 1.

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/articles.py` | Widget PHP |
| `app/services/tools/articles.py` (nou) | RAG |
| Extensió `row_to_card` per `article` | Tests integració batch 2 (issue final) |
| Registre a `ALL_TOOLS` + `_EXECUTORS` | Migrar routes/experiences |
| Documentar SQL provada a `sql-mapeo.md` §2 | |

## Criterios de aceptación

- [ ] `ArticlesRepository.search()` executa SQL §2 sense error en MySQL strict
- [ ] Tool `search_articles` retorna wrapper JSON (tecnic §6.13)
- [ ] `search_articles` registrat a `ALL_TOOLS`
- [ ] `row_to_card(..., 'article')` genera URL `https://www.femturisme.cat/noticies/{slug}` (hipòtesi Q-05)
- [ ] Sense import de `scraper.py`
- [ ] `python -m pytest -v` passa (suite existent)

## Capas / archivos principales

- `app/db/repositories/articles.py`
- `app/services/tools/articles.py`
- `app/db/mappers.py` — content type `article`
- `app/services/tools/__init__.py`
- `docs/sql-mapeo.md` §2

## Verificación

```powershell
python -m pytest -v
python -c "from dotenv import load_dotenv; load_dotenv(); from app.db.repositories import articles; ..."
```

## Issues relacionadas

- [#13](https://github.com/3urega/femturisme/issues/13) RoutesRepository
- [#15](https://github.com/3urega/femturisme/issues/15) Registry 6 MySQL
- [#17](https://github.com/3urega/femturisme/issues/17) Tests integració batch 2

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.2
- [sql-mapeo.md](../sql-mapeo.md) §2
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-203, DEV-303
- [plan-fase3-batch2-mysql.md](../devs/plan-fase3-batch2-mysql.md)
