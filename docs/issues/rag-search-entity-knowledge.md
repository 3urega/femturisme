## Objetivo

Cerca semàntica per `entity_id` i tool `search_entity_knowledge` operativa (substitueix dummy `search_local_knowledge`). Tanca **DEV-505**.

## Contexto

- Només es consulten chunks de documents amb `guide_documents.status = indexed`.
- Tool registrada a `ALL_TOOLS` però **exclosa** del xat públic (`CATALOG_TOOLS` / DEV-600).
- Disponible via `POST /admin/api/documents/{doc_id}/smoke-test` i mode entitat futur (Fase 7).
- Nom canònic: `search_entity_knowledge` ([tecnic.md](../client/tecnic.md) §6.12).

## Alcance

| In | Fuera |
|----|-------|
| `DocumentsRepository.search(query, entity_id, top_k)` amb pgvector (`<->` o cosinus) | Exposar tool al LLM en mode femturisme (DEV-702) |
| Tool `search_entity_knowledge` amb SCHEMA + `execute()` | RAG condicional per `entity_id` al catàleg |
| `POST /admin/api/documents/{doc_id}/smoke-test` | Retirar `search_local_knowledge` dummy (opcional aquest issue o cleanup) |
| Retorn JSON: chunks amb `content`, `metadata` (doc_title, page, source_file) | Indexació catàleg MySQL |

## Criterios de aceptación

- [ ] Smoke-test sobre document `indexed` retorna ≥1 chunk rellevant per query de prova
- [ ] Cerca filtrada per `entity_id`; no retorna chunks d'altres entitats
- [ ] `search_entity_knowledge` registrada; **no** apareix a `CATALOG_TOOLS` ni al prompt públic
- [ ] Test unitari/integració `tests/integration/rag/test_search_entity_knowledge.py`
- [ ] Checklist **DEV-505** marcat

## Capas / archivos principales

- `app/db/repositories/documents.py` (mètode `search`)
- `app/services/tools/entity_knowledge.py` (nou; o refactor `local_knowledge.py`)
- `app/services/tools/__init__.py`
- `app/routes/admin.py` — smoke-test
- `tests/integration/rag/test_search_entity_knowledge.py`

## Issues relacionadas

- `rag-indexing-pipeline.md` (prerequisit)
- `rag-admin-ui-uat.md` (següent)

## Verificación

```powershell
python -m pytest tests/integration/rag/test_search_entity_knowledge.py -v
python -m pytest tests/unit/test_tools_registry.py -v  # 6 catalog + entity no al públic
curl -s -X POST http://127.0.0.1:5010/admin/api/documents/<doc_id>/smoke-test -H "Content-Type: application/json" -d "{\"query\":\"on aparcar\"}"
```

## Referencias

- [tecnic.md](../client/tecnic.md) §6.12, §7.5
- [AGENTS.md](../../AGENTS.md) — `search_entity_knowledge`
- [estado-actual-vs-objetivo.md](../arquitectura/estado-actual-vs-objetivo.md)
