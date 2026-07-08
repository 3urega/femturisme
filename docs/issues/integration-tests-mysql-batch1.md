## Objetivo

Crear i executar **tots els tests** del batch fase3-prep quan hi hagi MySQL amb dades (dump client o staging). Desbloqueja la validació SQL real sense aturar la implementació de codi.

## Contexto

- Les issues #5–#10 implementen **codi** (mappers, repositories, tools, registry, prompt).
- Sense dump MySQL, els tests d'integració són l'únic bloqueig per validar resultats reals.
- Aquesta issue es tanca **al final del batch**, quan `MYSQL_HOST` + dades estiguin disponibles.
- Checklist: **DEV-202**, **DEV-204**, **DEV-205** (mapatges SQL) + validació parcial **DEV-302**, **DEV-304**, **DEV-305**.

## Alcance

| In | Fuera |
|----|-------|
| `tests/unit/test_mappers.py` (mock, sense MySQL) | SQL-03, SQL-06, SQL-07 (batch 2) |
| `tests/integration/sql/test_establishments.py` (SQL-01, SQL-02) | Tests E2E xat complet |
| `tests/integration/sql/test_destinations.py` (SQL-04) | Configurar MySQL staging (prereq extern) |
| `tests/integration/sql/test_events.py` (SQL-05) | |
| `tests/unit/test_prompts.py` (contingut mínim system prompt) | |
| Actualitzar [testing.md](../devs/testing.md) si cal | |

## Prerequisits

- Issues #5–#10 implementades (codi mergejat).
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` configurats (`.env` o staging).
- Dump o BD amb dades representatives (Girona, Pals, Besalú, Empordà…).

## Criterios de aceptación

- [ ] `tests/unit/test_mappers.py` passa sense MySQL
- [ ] `tests/unit/test_prompts.py` passa sense MySQL
- [ ] SQL-01 (Girona hotel) passa amb MySQL
- [ ] SQL-02 (Pals restaurant) passa amb MySQL
- [ ] SQL-04 (Besalú) passa amb MySQL
- [ ] SQL-05 (Empordà cap de setmana) passa amb MySQL
- [ ] Sense `MYSQL_HOST`: tests `@integration` es salten; `python -m pytest -v` passa
- [ ] Amb MySQL: `python -m pytest -m integration -v` passa

## Capas / archivos principales

- `tests/unit/test_mappers.py`
- `tests/unit/test_prompts.py`
- `tests/integration/sql/test_establishments.py`
- `tests/integration/sql/test_destinations.py`
- `tests/integration/sql/test_events.py`
- `tests/helpers/env.py` (si cal ampliar `mysql_available()`)

## Verificación

```powershell
# Sense MySQL (CI local)
python -m pytest -v

# Amb MySQL + dades
python -m pytest tests/unit/test_mappers.py tests/unit/test_prompts.py -v
python -m pytest -m integration -v
python scripts/test_sql_queries.py --ping
```

## Issues relacionadas

- #5 mappers · #6 establishments · #7 events · #8 destinations · #10 system prompt

## Referencias

- [testing.md](../devs/testing.md) §Tests SQL
- [sql-mapeo.md](../sql-mapeo.md) casos prova SQL-01/02/04/05
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-202, DEV-204, DEV-205
- [plan-fase3-prep-sense-mysql.md](../devs/plan-fase3-prep-sense-mysql.md)
