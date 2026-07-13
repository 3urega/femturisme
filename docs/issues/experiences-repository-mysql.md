## Objetivo

Migrar **`search_experiences`** de scraping a **MySQL** via `ExperiencesRepository` sobre taules `oferta_*` (DEV-206, DEV-301). Semàntica: experiències **promocionals**, no agenda.

## Contexto

- Checklist: **DEV-206**, **DEV-301**
- Tool actual: `app/services/tools/experiences.py` — SCHEMA legacy ambiguu; el prompt (#10) ja distingeix agenda vs experiències.
- SQL borrador: [sql-mapeo.md](../sql-mapeo.md) §6 — cas prova **SQL-06** (Olvan).
- Hipòtesi schema Q-04: `oferta_general` + FK `id_establiment` / `id_poble`.
- Atenció: filtres `data_final = '0000-00-00'` cal strict-safe (com establishments batch 1).

## Alcance

| In | Fuera |
|----|-------|
| `app/db/repositories/experiences.py` | Agenda (`search_events`) |
| Refactor `experiences.py` tool sense scraper | Registry/scraper delete |
| Mapper `experience` | Actualitzar SCHEMA tool (opcional; fora si no cal) |
| `sql-mapeo.md` §6 actualitzat | Tests batch 2 |

## Criterios de aceptación

- [ ] `ExperiencesRepository.search()` retorna ofertes vigents per destinació
- [ ] `experiences.py` sense import `scraper`
- [ ] Cards amb URL hipòtesi `https://www.femturisme.cat/ofertes/{slug}` (Q-05 TBD)
- [ ] SQL strict mode OK contra Railway
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/db/repositories/experiences.py`
- `app/services/tools/experiences.py`
- `app/db/mappers.py`
- `docs/sql-mapeo.md` §6

## Verificación

```powershell
python -m pytest -v
```

## Issues relacionadas

- [#13](https://github.com/3urega/femturisme/issues/13) RoutesRepository
- [#15](https://github.com/3urega/femturisme/issues/15) Registry 6 MySQL
- [#17](https://github.com/3urega/femturisme/issues/17) Tests integració batch 2

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §3.1, §4.6
- [sql-mapeo.md](../sql-mapeo.md) §6
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-206, DEV-301
