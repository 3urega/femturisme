## Objetivo

Afegir paràmetre opcional **`distance_km`** a `search_experiences` per cercar ofertes promocionals dins d'un radi des de `destination`, alineat amb el portal (`ubicacio` + `distancia`).

## Contexto

- Depèn del helper radi ([#1](geo-radius-helper.md))
- Repository actual: [`app/db/repositories/experiences.py`](../../app/db/repositories/experiences.py) — filtre territorial LIKE
- Tool: [`app/services/tools/experiences.py`](../../app/services/tools/experiences.py) — `destination`, `category`, `establishment`
- Cas d'ús: «Visitas guiadas a 50 km de Calella» → `category=Visites guiades`, `distance_km=50`

## Alcance

| In | Fuera |
|----|-------|
| `distance_km` opcional al SCHEMA i `execute()` | Altres tools de catàleg |
| `ExperiencesRepository.search(..., distance_km=)` usa Haversine quan present | Scraping `/ofertes` |
| `meta` amb `origin`, `distance_km`, `scope=radius` (o equivalent documentat) | Radi > 200 km (cap màxim documentat, p.ex. 100) |
| Tests integració: Calella + 50 km + Visites guiades → `total >= 1` (staging) | Canvis widget PHP |

## Criterios de aceptación

- [ ] SCHEMA inclou `distance_km` (integer, opcional, descripció «max distance in km from destination»)
- [ ] Amb `distance_km` sense coords d'origen → error JSON clar o fallback LIKE + `meta.hint`
- [ ] Resultats inclouen URL `https://www.femturisme.cat/ofertes/{param_url}`
- [ ] Sense `distance_km` → comportament idèntic al actual (regressió DEV-604 UAT-EXP-01)
- [ ] `pytest tests/integration/sql/test_experiences.py -v -m integration` verd (cas nou radi)

## Capas / archivos principales

- `app/db/repositories/experiences.py`
- `app/services/tools/experiences.py`
- `tests/integration/sql/test_experiences.py`
- `tests/unit/test_experiences_tool.py` (si cal)

## Issues relacionadas

- Prerequisit: `geo-radius-helper.md`
- Següent: `prompt-experiences-radius.md`, `uat-experiences-radius.md`

## Verificación

```powershell
python -m pytest tests/unit/test_experiences_tool.py tests/integration/sql/test_experiences.py -v
```

## Referencias

- [sql-mapeo.md](../sql-mapeo.md) §6
- [tecnic.md](../client/tecnic.md) §6 (contracte JSON card)
