# Pla: Fase 3 preparació sense dump MySQL

Treball executable **abans de tenir** dump de dades del client. Implementa codi, mappers, repositories amb SQL borrador i tests que es salten sense `MYSQL_HOST`.

**Estat:** publicades a GitHub (batch fase3-prep) · **Manifest:** [manifest.fase3-prep.json](../issues/manifest.fase3-prep.json)

**Prerequisits tancats:** Fase 1 base (#1–#4), `app/db/` esquelet (DEV-200), `sql-mapeo.md` borrador (DEV-010 parcial).

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

**Fora d'abast d'aquest batch:** articles, routes, experiences repositories; validar SQL amb dump real; RAG; PHP widget.

---

## Ordre d'implementació

```text
1. mappers-row-to-card           → DEV-208
2. establishments-repository     → DEV-302
3. events-repository             → DEV-305
4. destinations-repository       → DEV-304
5. tool-registry-legacy-cleanup  → DEV-307, DEV-308
6. system-prompt-6-domains       → DEV-310
```

---

## GitHub issues

| Ordre | GitHub | Títol | Checklist |
|-------|--------|-------|-----------|
| 1 | TBD | Fase 3 prep: row_to_card + wrapper JSON comú | DEV-208 |
| 2 | TBD | Fase 3 prep: EstablishmentsRepository + search_establishments | DEV-302 |
| 3 | TBD | Fase 3 prep: EventsRepository + search_events MySQL | DEV-305 |
| 4 | TBD | Fase 3 prep: DestinationsRepository + search_destinations | DEV-304 |
| 5 | TBD | Fase 3 prep: Registry 6 tools i eliminar scraping migrat | DEV-307, DEV-308 |
| 6 | TBD | Fase 3 prep: System prompt 6 dominis + idiomes | DEV-310 |

---

## Verificació global (sense MySQL)

```powershell
python -m pytest -v
python -m pytest -m integration -v
python scripts/test_sql_queries.py --ping
curl.exe -s http://127.0.0.1:5010/health
```

---

## Referències

- [sql-mapeo.md](../sql-mapeo.md)
- [preparacio-rag-cataleg.md](preparacio-rag-cataleg.md)
- [fase-3-tools-mysql-ca.md](../fase-3-tools-mysql-ca.md)
- [checklist-entrega.md](checklist-entrega.md)
