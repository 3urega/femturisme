## Objetivo

Actualitzar el registry de tools: registrar buscadors MySQL nous, treure legacy migrat i eliminar imports de `scraper.py` als tools ja migrats (DEV-307, DEV-308).

## Contexto

- Checklist: **DEV-307**, **DEV-308**
- Després de migrar establishments, events, destinations (#issues anteriors del batch).
- Avui `ALL_TOOLS` té 5 tools legacy (accommodations, experiences scraping, events scraping, routes scraping, local_knowledge dummy).
- Objectiu parcial: 3 tools MySQL + 2 legacy pendents (routes, experiences) fins batch següent.

## Alcance

| In | Fuera |
|----|-------|
| Registrar `search_establishments`, `search_destinations` a `__init__.py` | Migrar routes/experiences/articles (batch 2) |
| Treure `search_accommodations` del registry actiu | Eliminar fitxer `scraper.py` del repo |
| Verificar cap import scraper a establishments, events, destinations | `search_entity_knowledge` (Fase 5) |
| Actualitzar mocks de test si cal | Mode entitat / filtratge tools |

## Criterios de aceptación

- [ ] `ALL_TOOLS` inclou `search_establishments`, `search_events`, `search_destinations` (MySQL)
- [ ] `search_accommodations` no està al registry (substituït per establishments)
- [ ] Cap `from .scraper` a `establishments.py`, `events.py`, `destinations.py`
- [ ] `execute_tool()` resol els nous noms
- [ ] Tests API existents (API-01…05) passen amb mocks
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/services/tools/__init__.py`
- `app/services/tools/establishments.py`
- `app/services/tools/events.py`
- `app/services/tools/destinations.py`

## Verificación

```powershell
python -m pytest tests/api/ -v
python -m pytest -v
```

## Issues relacionadas

- `establishments-repository-mysql.md`
- `events-repository-mysql.md`
- `destinations-repository-mysql.md`
- `system-prompt-6-domains.md`

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §6
- [estado-actual-vs-objetivo.md](../arquitectura/estado-actual-vs-objetivo.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-307, DEV-308
