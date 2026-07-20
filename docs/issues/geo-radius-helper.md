## Objetivo

Implementar la **capa geo de radi km** reutilitzable: resoldre coordenades d'origen des de `destination` i generar predicat SQL Haversine per filtrar registres amb lat/lng coneguts.

Base per [#2 del batch](experiences-distance-km.md) (`search_experiences.distance_km`).

## Contexto

- Portal: `/ofertes?ubicacio=calella&distancia=50` — veure [plan-experiences-radius.md](../devs/plan-experiences-radius.md)
- Avui `resolve_geo_filter()` a [`app/db/territory.py`](../../app/db/territory.py) fa LIKE / llista `poble_ids`, **sense** distància
- Schema: `poble_general`, `establiment_general`, `generic_ubicacions` tenen `latitud`/`longitud` ([`docs/schema.sql`](../schema.sql))

## Alcance

| In | Fuera |
|----|-------|
| Helper `resolve_origin_coordinates(destination)` → `(lat, lng)` o None | Canvis a tools encara |
| Helper `haversine_km_predicate(origin, lat_col, lng_col)` → SQL + params | Radi a altres buscadors (establishments, events…) |
| Documentar SQL i casos prova a [`sql-mapeo.md`](../sql-mapeo.md) §6 (subsecció radi) | Text-to-SQL |
| Tests unitaris del helper (mock coords) + 1 test integració origen Calella (skip sense MySQL) | Reverse-engineer PHP CMS al 100% sense validar amb dades |

## Criterios de aceptación

- [ ] Resolució d'origen per municipi (`poble_general.param_url` o nom normalitzat)
- [ ] Predicat Haversine retorna clàusula SQL embeddable amb params segurs
- [ ] `distance_km` absent → cap canvi de comportament als repos existents
- [ ] `sql-mapeo.md` §6 documenta contracte i exemple Calella + 50 km
- [ ] `pytest tests/unit/test_geo_radius.py -v` (nou) verd

## Capas / archivos principales

- `app/db/territory.py` o `app/db/geo_radius.py` (nou mòdul si cal separar)
- `docs/sql-mapeo.md` §6
- `tests/unit/test_geo_radius.py`
- `tests/integration/sql/test_geo_radius.py` (opcional, `@pytest.mark.integration`)

## Issues relacionadas

- Següent: `experiences-distance-km.md`

## Verificación

```powershell
python -m pytest tests/unit/test_geo_radius.py -v
python -m pytest tests/integration/sql/test_geo_radius.py -v -m integration
```

## Referencias

- [plan-experiences-radius.md](../devs/plan-experiences-radius.md)
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.6
- [patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md)
