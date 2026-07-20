## Objectiu

Tancar la **deuda tècnica i ops** detectada a l’[auditoria Fase 5 RAG](../devs/auditoria-fase5-rag.md) després del batch DEV-500…507 (#27–#33). El nucli RAG funciona; aquest issue endurteix seguretat, disc, CLI, concurrencia i tests §14.4 pendents.

**Fora d’abast:** DEV-506 (gestor PHP CMS), mode entitat al xat (Fase 7), cola Redis/Celery completa.

---

## Context

Auditoria 2026-07-20 sobre pipeline, API admin, UI Flask, tool `search_entity_knowledge` i tests. Confirmat: happy path sòlid. Gaps accionables concentrats en ops/seguretat i paritat amb `plan-integracion-ca.md` §9.

---

## Alcance

| In | Fuera |
|----|-------|
| `scripts/ingest_pdf.py` (`--file`, `--list`, `--verify`) | DEV-506 PHP |
| Neteja `data/guides/{doc_id}/` en DELETE entity | Cola de jobs externa (Redis) |
| Protecció `/admin/guides*` + tests auth 401 | RAG condicional catàleg (DEV-702) |
| Lock per `doc_id` a `schedule_indexing` | Migració embedding model |
| Tests pytest §14.4 pendents | Reescriptura completa plan-integracion |
| Runbook `failed` → reindex a `docs/devs/` | |

---

## Criteris d’acceptació

### CLI i disc

- [ ] `scripts/ingest_pdf.py --file … --entity-id … --title …` indexa via `indexing_pipeline.run()` (paritat amb upload API)
- [ ] `--list` llista documents des de BD; `--verify {doc_id} --query …` crida smoke-test/search
- [ ] `DELETE /admin/api/entities/{id}` elimina fitxers PDF de tots els documents CASCADEats abans o després del DELETE BD

### Seguretat admin

- [ ] Rutas `/admin/guides*` exigeixen el mateix Bearer que `/admin/api/*` quan `ADMIN_API_TOKEN` està configurat (o documentar defer explícit + WAF)
- [ ] Tests: 401 sense token / token incorrecte amb `ADMIN_API_TOKEN` configurat (API com a mínim)

### Pipeline i consistència

- [ ] `schedule_indexing` ignora o serialitza segona crida concurrent sobre el mateix `doc_id`
- [ ] Decisió documentada: upload a entitat `is_active=false` → 400 o permès; search coherente

### Tests §14.4

- [ ] `PUT /admin/api/entities/{id}` (update camps, slug duplicat)
- [ ] `POST /admin/api/documents/{id}/reindex` → eventual `indexed` + `version+1` (mock embedder o poll)
- [ ] Document `failed` → reindex HTTP → `indexed`
- [ ] `DocumentsRepository.search` amb filtre `category` (test integració)

### Documentació

- [ ] Runbook breu: operador veu `failed` → logs → reindex → smoke-test (`docs/devs/runbook-rag-admin.md`)
- [ ] Actualitzar `plan-integracion-ca.md` §9: rutes `/admin/api/documents/*`, `entity_id`, estat CLI

---

## Fitxers principals

- `scripts/ingest_pdf.py` (nou)
- `app/routes/admin.py` — DELETE entity + neteja storage
- `app/routes/admin_ui.py` — auth HTML
- `app/services/indexing_pipeline.py` — lock doc_id
- `app/services/admin_auth.py` — reutilitzar per UI
- `tests/api/test_admin_auth.py`, `tests/integration/rag/test_reindex_http.py` (nous o ampliats)
- `docs/devs/runbook-rag-admin.md`

---

## Verificació

```powershell
python -m pytest tests/api/test_admin_auth.py tests/integration/rag/ -v -m integration
python scripts/ingest_pdf.py --list
python scripts/uat_rag_battery.py http://127.0.0.1:5010
```

---

## Referències

- [auditoria-fase5-rag.md](../devs/auditoria-fase5-rag.md)
- [tecnic.md](../client/tecnic.md) §10.3, §14.4
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9
- [checklist-entrega.md](../devs/checklist-entrega.md) — batch DEV-500…507 tancat
