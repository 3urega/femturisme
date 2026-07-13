## Objetivo

Completar **DEV-307** i **DEV-308**: registry amb **6 buscadors MySQL** de catàleg (+ `search_local_knowledge` stub), sense scraping ni `search_accommodations`.

## Contexto

- Post issues articles/routes/experiences del batch 2.
- #9 va fer neteja parcial (3 MySQL + 2 legacy scraping).
- `scraper.py` només es pot eliminar quan cap tool de catàleg l'importi.
- `accommodations.py` legacy: desregistrar o eliminar fitxer (ja fora del registry des de #9).

## Alcance

| In | Fuera |
|----|-------|
| `ALL_TOOLS` amb 6 MySQL: establishments, destinations, events, articles, routes, experiences | `search_local_knowledge` implementació real |
| + `search_local_knowledge` stub (com avui) | Mode entitat / RAG |
| Eliminar o marcar deprecated `scraper.py` si cap import | DEV-309 límits |
| Verificar cap `from .scraper` a tools de catàleg | Dummy keywords si cal (mínim) |

## Criterios de aceptación

- [ ] `ALL_TOOLS` llista exactament 6 noms objectiu de catàleg + local_knowledge
- [ ] Cap tool de catàleg importa `scraper.py`
- [ ] `rg "from \.scraper" app/services/tools/` → zero coincidències (o només deprecated explícit)
- [ ] `execute_tool` resol els 6 buscadors MySQL
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/services/tools/__init__.py`
- `app/services/tools/scraper.py` (eliminar o deprecated)
- `app/services/tools/accommodations.py` (opcional eliminar)

## Verificación

```powershell
python -m pytest -v
rg "from \.scraper" app/services/tools/
python -c "from app.services.tools import ALL_TOOLS; print([t['name'] for t in ALL_TOOLS])"
```

## Issues relacionadas

- [#12](https://github.com/3urega/femturisme/issues/12) ArticlesRepository
- [#13](https://github.com/3urega/femturisme/issues/13) RoutesRepository
- [#14](https://github.com/3urega/femturisme/issues/14) ExperiencesRepository
- [#16](https://github.com/3urega/femturisme/issues/16) System prompt articles

## Referencias

- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-307, DEV-308
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §5
