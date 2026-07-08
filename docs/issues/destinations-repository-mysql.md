## Objetivo

Afegir el buscador **on anar**: `DestinationsRepository` + tool `search_destinations` (DEV-304).

## Contexto

- Checklist: **DEV-304**
- SQL borrador: [sql-mapeo.md §3](../sql-mapeo.md) (`poble_*`, `poble_continguts`).
- Avui **no existeix** tool de destinacions al registry (només legacy scraping parcial via altres tools).
- Depèn de: `mappers-row-to-card.md`.

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/destinations.py` | Query `generic_ubicacions` (opcional, fase posterior) |
| Nou `app/services/tools/destinations.py` | Confondre amb establiments o articles |
| | Tests SQL-04 (issue final) |

## Criterios de aceptación

- [ ] Tool SCHEMA: `destination` (required), `region?`, `lang?`
- [ ] Repository SQL §3 amb filtres territori
- [ ] Cards amb `source_type=destination`, `location` = comarca
- [ ] Sense MySQL: error JSON amigable
- [ ] `python -m pytest -v` passa (suite existent)

## Capas / archivos principales

- `app/db/repositories/destinations.py`
- `app/services/tools/destinations.py`

## Verificación

```powershell
python -m pytest -v
```

## Issues relacionadas

- `mappers-row-to-card.md`
- `tool-registry-legacy-cleanup.md`

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.3
- [sql-mapeo.md](../sql-mapeo.md) §3
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-304
