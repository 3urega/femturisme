# Pla: Fase 3 preparació sense dump MySQL

Treball executable **abans de tenir** dump de dades del client. Implementa codi, mappers, repositories amb SQL borrador. **Tests** (unit + integració MySQL) queden per issue final #11 quan hi hagi dades.

**Estat:** publicades a GitHub (batch fase3-prep) · **Manifest:** [manifest.fase3-prep.json](../issues/manifest.fase3-prep.json)

**Prerequisits tancats:** Fase 1 base (#1–#4), `app/db/` esquelet (DEV-200), `sql-mapeo.md` borrador (DEV-010 parcial), **mappers** (#5, DEV-208, 2026-07-08).

---

## Implementat

| GitHub | Item | Data |
|--------|------|------|
| [#5](https://github.com/3urega/femturisme/issues/5) | `row_to_card()` + `build_search_wrapper()` — DEV-208 | 2026-07-08 |

---

## Objectiu

| Què | Per què |
|-----|---------|
| `row_to_card()` + wrapper JSON | DEV-208 — base per tots els repositories |
| `EstablishmentsRepository` + tool | DEV-302 — primer slice vertical (substitueix accommodations) |
| `EventsRepository` + tool | DEV-305 — agenda amb filtres de data |
| `DestinationsRepository` + tool | DEV-304 — on anar (nou buscador) |
| Neteja registry legacy | DEV-307, DEV-308 — cap scraper als tools migrats |
| System prompt 6 dominis | DEV-310 — routing LLM correcte |
| Tests MySQL batch 1 | DEV-202, DEV-204, DEV-205 — SQL-01/02/04/05 + unit tests (al final) |

**Fora d'abast d'aquest batch:** articles, routes, experiences repositories; RAG; PHP widget.

---

## Ordre d'implementació

```text
1. mappers-row-to-card           → DEV-208
2. establishments-repository     → DEV-302
3. events-repository             → DEV-305
4. destinations-repository       → DEV-304
5. tool-registry-legacy-cleanup  → DEV-307, DEV-308
6. system-prompt-6-domains       → DEV-310
7. integration-tests-mysql-batch1 → DEV-202, DEV-204, DEV-205  (quan hi hagi MySQL + dades)
```

---

## GitHub issues

| Ordre | GitHub | Títol | Checklist |
|-------|--------|-------|-----------|
| 1 | [#5](https://github.com/3urega/femturisme/issues/5) ✅ | Fase 3 prep: row_to_card + wrapper JSON comú | DEV-208 |
| 2 | [#6](https://github.com/3urega/femturisme/issues/6) | Fase 3 prep: EstablishmentsRepository + search_establishments | DEV-302 |
| 3 | [#7](https://github.com/3urega/femturisme/issues/7) | Fase 3 prep: EventsRepository + search_events MySQL | DEV-305 |
| 4 | [#8](https://github.com/3urega/femturisme/issues/8) | Fase 3 prep: DestinationsRepository + search_destinations | DEV-304 |
| 5 | [#9](https://github.com/3urega/femturisme/issues/9) | Fase 3 prep: Registry 6 tools i eliminar scraping migrat | DEV-307, DEV-308 |
| 6 | [#10](https://github.com/3urega/femturisme/issues/10) | Fase 3 prep: System prompt 6 dominis + idiomes | DEV-310 |
| 7 | [#11](https://github.com/3urega/femturisme/issues/11) | Fase 3 prep: Tests integració MySQL batch 1 | DEV-202, DEV-204, DEV-205 |

---

## Verificació global (implementació, sense nous tests)

```powershell
python -m pytest -v
curl.exe -s http://127.0.0.1:5010/health
```

Quan es tanqui #11 (amb MySQL):

```powershell
python -m pytest -m integration -v
python scripts/test_sql_queries.py --ping
```

---

## Referències

- [sql-mapeo.md](../sql-mapeo.md)
- [preparacio-rag-cataleg.md](preparacio-rag-cataleg.md)
- [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md)
- [checklist-entrega.md](checklist-entrega.md)
