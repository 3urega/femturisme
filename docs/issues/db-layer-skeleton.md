## Objetivo

Crear l'esquelet de la capa de dades `app/db/` segons [capas-y-modulos.md](../arquitectura/capas-y-modulos.md): connexió, mappers i carpeta repositories, preparats per Fase 3 sense dependre del schema MySQL del client.

## Contexto

- Checklist: **DEV-200**
- Avui **no existeix** `app/db/`; les tools criden scraping legacy.
- Aquest issue crea l'estructura i funcions `ping_mysql()` / `ping_postgres()` per health i script `scripts/test_sql_queries.py --ping`.
- Depèn de: `config-env-example`, `requirements-db-deps`.

## Alcance

| In | Fuera |
|----|-------|
| `app/db/__init__.py` | Repositories amb SQL real (Fase 3) |
| `app/db/connection.py` — `get_mysql_connection()`, `ping_mysql()`, `ping_postgres()` | Pools avançats / SQLAlchemy |
| `app/db/mappers.py` — stub `row_to_card()` + docstring contracte tecnic §6.13 | `row_to_card()` complet |
| `app/db/repositories/__init__.py` (buit o package marker) | Fitxers per buscador |
| Actualitzar `scripts/test_sql_queries.py --ping` per usar `connection.ping_mysql()` | Tests integració SQL (ja placeholders) |
| Test unitari: ping retorna `skipped`/`not_configured` si falten MYSQL_* | |

| Fuera | |
|----|-------|
| Queries SQL | |
| Substituir scraping a tools | |
| Text-to-SQL | |

## Criterios de aceptación

- [ ] Estructura `app/db/` com a [capas-y-modulos.md](../arquitectura/capas-y-modulos.md)
- [ ] `ping_mysql()`: si `MYSQL_HOST` buit → estat `not_configured` (no exception)
- [ ] `ping_mysql()`: si configurat → intent connexió `SELECT 1` amb timeout de config
- [ ] `ping_postgres()`: mateix patró per `POSTGRES_*`
- [ ] `mappers.py` defineix signatura `row_to_card(row, content_type)` (stub o NotImplementedError documentat)
- [ ] `python scripts/test_sql_queries.py --ping` exit 0 (missatge clar si no configurat o OK si staging disponible)
- [ ] `python -m pytest -v` passa (afegir test unitari `tests/unit/test_db_connection.py` si cal)

## Capas / archivos principales

- `app/db/__init__.py`
- `app/db/connection.py`
- `app/db/mappers.py`
- `app/db/repositories/__init__.py`
- `scripts/test_sql_queries.py`
- `tests/unit/test_db_connection.py` (nou, opcional però recomanat)

## Verificación

```powershell
python scripts/test_sql_queries.py --ping
python -m pytest -v
python -c "from app.db.connection import ping_mysql; print(ping_mysql())"
```

## Issues relacionadas

- `config-env-example.md`
- `requirements-db-deps.md`
- `health-endpoint.md` — consumeix ping

## Referencias

- [patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md)
- [estado-actual-vs-objetivo.md](../arquitectura/estado-actual-vs-objetivo.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-200
- [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md)
