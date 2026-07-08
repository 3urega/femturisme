## Objetivo

Migrar `search_events` de scraping a `EventsRepository` MySQL amb filtres de calendari (DEV-305).

## Contexto

- Checklist: **DEV-305**
- SQL borrador: [sql-mapeo.md §5](../sql-mapeo.md) (`agenda_*`).
- Domini: **agenda** (esdeveniments amb data) — no confondre amb experiències promocionals.
- Depèn de: `mappers-row-to-card.md`, `connection.py`.

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/events.py` | `search_experiences` / `oferta_*` |
| Refactor `app/services/tools/events.py` sense scraper | Esdeveniments periòdics complexos (TBD client) |
| Filtres `date_from`, `date_to` sobre `agenda_dates` | RAG |
| | Tests SQL-05 (issue final) |

## Criterios de aceptación

- [ ] Repository implementa SQL §5 amb paràmetres bindats
- [ ] Tool manté SCHEMA: `destination`, `date_from?`, `date_to?`
- [ ] Cards inclouen `date` (rang formatat) i `source_type=event`
- [ ] Sense MySQL: error JSON amigable, no scraper
- [ ] `python -m pytest -v` passa (suite existent)

## Capas / archivos principales

- `app/db/repositories/events.py`
- `app/services/tools/events.py`

## Verificación

```powershell
python -m pytest -v
```

## Issues relacionadas

- `mappers-row-to-card.md`
- `tool-registry-legacy-cleanup.md`

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §3.1, §4.5
- [sql-mapeo.md](../sql-mapeo.md) §5
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-305
