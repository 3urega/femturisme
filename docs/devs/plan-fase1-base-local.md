# Pla: Fase 1 base local (sense esperar client)

Treball executable **abans de tenir** MySQL staging del client. Tanca gaps de Fase 1 i prepara Fase 2–3.

**Estat:** publicades a GitHub (2026-07-03) · **Implementades:** #1 (2026-07-07), #2 (2026-07-08), #3 (2026-07-08), #4 (2026-07-08) · **Manifest:** [manifest.fase1-base-local.json](../issues/manifest.fase1-base-local.json)

---

## Objectiu

| Què | Per què |
|-----|---------|
| Config + `.env.example` complets | DEV-102, DEV-109 |
| Drivers DB a `requirements.txt` | DEV-101 |
| Esquelet `app/db/` | DEV-200 |
| `GET /health` | DEV-103, prereq DEV-108 |

**Fora d'abast:** repositories amb SQL, substituir scraping, accés MySQL client (Fase A).

---

## Ordre d'implementació

```text
1. config-env-example     → DEV-102, DEV-109
2. requirements-db-deps    → DEV-101
3. db-layer-skeleton      → DEV-200
4. health-endpoint        → DEV-103
```

---

## GitHub issues (publicades)

| Ordre | GitHub | Títol | Checklist | Estat |
|-------|--------|-------|-----------|-------|
| 1 | [#1](https://github.com/3urega/femturisme/issues/1) | Config completa app/config.py + .env.example | DEV-102, DEV-109 | Implementada |
| 2 | [#2](https://github.com/3urega/femturisme/issues/2) | requirements.txt amb drivers MySQL i PostgreSQL | DEV-101 | Implementada |
| 3 | [#3](https://github.com/3urega/femturisme/issues/3) | Esquelet app/db | DEV-200 | Implementada |
| 4 | [#4](https://github.com/3urega/femturisme/issues/4) | GET /health | DEV-103 | Implementada |

Drafts locals: [docs/issues/](../issues/) (eliminar quan es tanquin les issues).

---

## Verificació global (post-batch)

```powershell
python -m pip install -r requirements.txt
python -m pytest -v
python main.py
curl.exe -s http://127.0.0.1:5010/health
python scripts/test_sql_queries.py --ping
```

---

## Següent batch (bloquejat client)

Fase A: DEV-020…022 (schema MySQL, `agent_read`, staging) → després Fase 2 `sql-mapeo.md` i Fase 3 primer repository.

---

## Referències

- [checklist-entrega.md](checklist-entrega.md)
- [desenvolupament-local.md](desenvolupament-local.md)
- [tecnic.md §9.3, §10](../client/tecnic.md)
