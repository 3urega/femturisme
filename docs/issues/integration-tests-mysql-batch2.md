## Objetivo

Executar i tancar la validació MySQL del **batch 2**: tests integració **SQL-03, SQL-06, SQL-07** + ampliació unit tests mappers si cal (DEV-203, DEV-206, DEV-207 + repos).

## Contexto

- #11 va validar SQL-01/02/04/05 contra Railway.
- Placeholders existents: `test_articles.py`, `test_experiences.py`, `test_routes.py`.
- Prerequisit: repositories articles, routes, experiences implementats + registry actualitzat.
- Patró strict mode ja conegut del batch 1.

## Alcance

| In | Fuera |
|----|-------|
| `pytest -m integration` SQL-03/06/07 verds amb MySQL | SQL batch 1 (ja fet) |
| Asserts `int(total) >= 0` coherents | E2E xat |
| Marcar sql-mapeo §2/6/7 casos prova ☑ | DEV-309 |
| Actualitzar `testing.md` si cal | |

## Criterios de aceptación

- [ ] `test_articles_parc_cadi` passa amb MySQL
- [ ] `test_experiences_olvan` passa amb MySQL
- [ ] `test_routes_emporda_foot` passa amb MySQL
- [ ] Sense `MYSQL_HOST`: integration skipped; `pytest -v` default passa
- [ ] Amb MySQL: `python -m pytest -m integration -v` passa (batch 1 + 2)
- [ ] DEV-203, DEV-206, DEV-207, DEV-301, DEV-303, DEV-306 Detect al checklist

## Capas / archivos principales

- `tests/integration/sql/test_articles.py`
- `tests/integration/sql/test_experiences.py`
- `tests/integration/sql/test_routes.py`
- `app/db/mappers.py` (si cal tipus nous)
- `docs/sql-mapeo.md`
- `docs/devs/checklist-entrega.md`

## Verificación

```powershell
python -m pytest -v
python -m pytest tests/integration/sql/test_articles.py tests/integration/sql/test_experiences.py tests/integration/sql/test_routes.py -m integration -v
python -m pytest -m integration -v
python scripts/test_sql_queries.py --ping
```

## Issues relacionadas

- [#12](https://github.com/3urega/femturisme/issues/12)…[#16](https://github.com/3urega/femturisme/issues/16) (repos + registry + prompt)

## Referencias

- [testing.md](../devs/testing.md)
- [plan-fase3-batch2-mysql.md](../devs/plan-fase3-batch2-mysql.md)
- Issue #11 (batch 1 tests)
