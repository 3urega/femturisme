## Objetivo

Afegir paràmetre opcional `distance_km` a `search_establishments` per cercar allotjament (i restauració) dins d'un radi geogràfic des d'un punt, amb paritat al portal i al batch radi d'experiències ([#41](https://github.com/3urega/femturisme/issues/41)–[#44](https://github.com/3urega/femturisme/issues/44)).

## Contexto

A la conversa reportada l'agent va proposar «30 km des de Berga» però la tool només acceptava `destination=Berga` (filtre territorial estret). El helper Haversine ja existeix a [`app/db/geo_radius.py`](../../app/db/geo_radius.py).

Documentació domini: dormir + menjar = un buscador (`search_establishments`); proximitat geogràfica amb km conegut ha d'incloure radi quan el paràmetre existeixi.

## Alcance

| In | Fuera |
|----|-------|
| `distance_km` a `EstablishmentsRepository.search()` + SQL Haversine | Radi a `search_experiences` (ja fet #42) |
| SCHEMA + `execute()` a [`app/services/tools/establishments.py`](../../app/services/tools/establishments.py) | Panell admin / PHP |
| Secció `sql-mapeo.md` (establiments + radi) | Heurística server-side d'injectar km (opcional futur) |
| Tests integració MySQL (cas Berga ~30 km) | Prompt (issue #45; actualització post-implementació a part) |

## Criterios de aceptación

- [ ] `search_establishments` accepta `distance_km` (enter, clamp coherent amb experiences, p.ex. 100).
- [ ] Amb `destination=Berga` + `distance_km=30` retorna establiments dins del radi (`meta.scope=radius` o equivalent).
- [ ] Sense `distance_km` es manté comportament territorial actual (no regressió).
- [ ] `pytest tests/integration/sql/test_establishments.py -m integration` passa (cas radi nou).
- [ ] `sql-mapeo.md` documenta paràmetres i SQL.

## Capas / archivos principales

- [`app/db/geo_radius.py`](../../app/db/geo_radius.py) (reutilitzar)
- [`app/db/repositories/establishments.py`](../../app/db/repositories/establishments.py)
- [`app/services/tools/establishments.py`](../../app/services/tools/establishments.py)
- [`docs/sql-mapeo.md`](../sql-mapeo.md)
- [`tests/integration/sql/test_establishments.py`](../../tests/integration/sql/test_establishments.py)

## Issues relacionadas

- #45 — prompt genèric sense cases-rurals
- #49 — UAT conversa

## Referencias

- [tecnic.md §6](../../client/tecnic.md)
- [plan-experiences-radius.md](../devs/plan-experiences-radius.md)
- [plan-establishments-proximity.md](../devs/plan-establishments-proximity.md)

## Verificación

```bash
pytest tests/integration/sql/test_establishments.py -v -m integration -k radius
pytest tests/unit/test_establishments_tool.py -q
```
