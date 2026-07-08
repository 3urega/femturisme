## Objetivo

Primer slice vertical MySQL: `EstablishmentsRepository` + tool `search_establishments` (dormir + menjar unificat), substituint `search_accommodations` (DEV-302).

## Contexto

- Checklist: **DEV-302**
- SQL borrador: [sql-mapeo.md §1](../sql-mapeo.md) (`establiment_*`, `generic_tipus_establiment`).
- Depèn de: `mappers-row-to-card.md`, `app/db/connection.py` (#3).
- **No cal dump MySQL** per mergear: només codi; tests a issue final `integration-tests-mysql-batch1.md`.

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/establishments.py` amb SQL parametritzada | Eliminar `accommodations.py` (issue registry) |
| `app/services/tools/establishments.py` (`search_establishments`) | Validar URLs Q-05 amb client |
| Refactor `execute()` sense `scraper.py` | Articles, routes, experiences |
| | Tests SQL-01/02 (issue final) |

## Criterios de aceptación

- [ ] Repository: només `SELECT`, paràmetres bindats, `LIMIT 20`
- [ ] Tool SCHEMA amb `destination` (required), `type?`, `lang?` (default `ca`)
- [ ] Sortida JSON normalitzada via mappers (`source_type=establishment`)
- [ ] Sense `MYSQL_HOST`: tool retorna `{error: "...", results: []}` sense excepció
- [ ] `python -m pytest -v` passa (suite existent)

## Capas / archivos principales

- `app/db/repositories/establishments.py`
- `app/services/tools/establishments.py`

## Verificación

```powershell
python -m pytest -v
```

## Issues relacionadas

- `mappers-row-to-card.md`
- `tool-registry-legacy-cleanup.md`

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.1
- [sql-mapeo.md](../sql-mapeo.md) §1
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-302
