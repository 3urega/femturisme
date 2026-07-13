## Objetivo

Migrar **`search_routes`** de scraping a **MySQL** via `RoutesRepository` (DEV-207, DEV-306).

## Contexto

- Checklist: **DEV-207**, **DEV-306**
- Tool actual: `app/services/tools/routes_tool.py` importa `scraper.py`.
- SQL borrador: [sql-mapeo.md](../sql-mapeo.md) §7 — cas prova **SQL-07** (Empordà, A peu).
- Patró: mateix que establishments/events (repository + refactor `execute()`).

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/routes.py` | `search_articles` |
| Refactor `routes_tool.py` sense scraper | Registry final (issue següent) |
| Mapper `route` a `mappers.py` | Tests batch 2 |
| Actualitzar `sql-mapeo.md` §7 | Eliminar `scraper.py` del repo |

## Criterios de aceptación

- [ ] `RoutesRepository.search()` retorna wrapper amb cards URL `https://www.femturisme.cat/rutes/{slug}`
- [ ] `routes_tool.py` sense `from .scraper`
- [ ] Filtre `type` (A peu, bici…) mapejat segons `generic_tematiques` / sql-mapeo
- [ ] SQL compatible MySQL 8 strict (GROUP BY / dates)
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/db/repositories/routes.py`
- `app/services/tools/routes_tool.py`
- `app/db/mappers.py`
- `docs/sql-mapeo.md` §7

## Verificación

```powershell
python -m pytest -v
```

## Issues relacionadas

- [#12](https://github.com/3urega/femturisme/issues/12) ArticlesRepository
- [#14](https://github.com/3urega/femturisme/issues/14) ExperiencesRepository
- [#15](https://github.com/3urega/femturisme/issues/15) Registry 6 MySQL

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.4
- [sql-mapeo.md](../sql-mapeo.md) §7
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-207, DEV-306
