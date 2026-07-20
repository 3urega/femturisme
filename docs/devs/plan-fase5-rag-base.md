# Pla: Fase 5 — Infra RAG (PDFs, embeddings, pgvector)

Construir la **base de coneixement documental** al servei Python: PostgreSQL + pgvector, APIs admin, pipeline d'indexació i tool `search_entity_knowledge`.

**Estat:** batch publicat a GitHub *(2026-07-14)*.

**Prerequisits tancats:** 6 buscadors MySQL (Fase 3), mode femturisme sense RAG públic (DEV-600), CA verificats (DEV-605).

**Entorn objectiu v1:** desenvolupament local (PostgreSQL + OpenAI embeddings). Staging remot (DEV-023) es pot fer en paral·lel quan hi hagi accés.

---

## Ordre d'implementació

1. **Schema PostgreSQL local** (DEV-500) — `entities`, `guide_documents`, `document_chunks` + pgvector
2. **API CRUD entitats** (DEV-501) — `/admin/api/entities`
3. **Pujada PDF + emmagatzematge** (DEV-502, DEV-503) — `/admin/api/documents/*`
4. **Pipeline indexació** (DEV-504) — extract → chunk → embed → `indexed`
5. **Cerca semàntica + tool** (DEV-505) — `DocumentsRepository`, `search_entity_knowledge`
6. **Panell admin Flask + UAT intern** (DEV-507) — operació sense PHP

La Fase 4 (widget PHP) i **DEV-506** (gestor documental al CMS PHP) romanen **fora** d'aquest batch.

---

## Decisions congelades

| Tema | Decisió |
|------|---------|
| Vector store | **pgvector** a la mateixa PostgreSQL agent |
| Model embedding | `text-embedding-3-small` (1536 dims) — `EMBEDDING_MODEL` a config |
| Tool RAG | `search_entity_knowledge` (alias legacy `search_municipality_guides`) |
| Xat públic Fase 1 | Tool **no** exposada al LLM (`CATALOG_TOOLS`); DEV-600 ja aplicat |
| RAG condicional catàleg | Fase 7 (DEV-702); **no** en aquest batch |
| RAG semàntic catàleg MySQL | Futur — [preparacio-rag-cataleg.md](preparacio-rag-cataleg.md); batch separat |

---

## GitHub issues (draft → publicat)

| Slug | Títol | Labels | DEV | Depèn de |
|------|-------|--------|-----|----------|
| `rag-postgres-schema.md` | Fase 5: Schema PostgreSQL agent + pgvector local (DEV-500) | fase-5, postgres, rag, infra | DEV-500 | — | [#27](https://github.com/3urega/femturisme/issues/27) **tancat** *(2026-07-20)* |
| `rag-entities-api.md` | Fase 5: API CRUD entitats /admin/api/entities (DEV-501) | fase-5, postgres, rag, api | DEV-501 | DEV-500 | [#28](https://github.com/3urega/femturisme/issues/28) |
| `rag-documents-upload.md` | Fase 5: API documents i emmagatzematge PDF (DEV-502, DEV-503) | fase-5, postgres, rag, api | DEV-502, DEV-503 | DEV-501 | [#29](https://github.com/3urega/femturisme/issues/29) |
| `rag-indexing-pipeline.md` | Fase 5: Pipeline indexació PDF extract/chunk/embed (DEV-504) | fase-5, rag, agent | DEV-504 | DEV-503 | [#33](https://github.com/3urega/femturisme/issues/33) |
| `rag-search-entity-knowledge.md` | Fase 5: DocumentsRepository i search_entity_knowledge (DEV-505) | fase-5, rag, postgres, agent | DEV-505 | DEV-504 | [#31](https://github.com/3urega/femturisme/issues/31) |
| `rag-admin-ui-uat.md` | Fase 5: Panell admin Flask i UAT intern RAG (DEV-507) | fase-5, rag, testing | DEV-507 | DEV-505 | [#32](https://github.com/3urega/femturisme/issues/32) |

Manifest: [manifest.fase5-rag.json](../issues/manifest.fase5-rag.json)

---

## Fora d'abast d'aquest batch

- Widget globus / proxy PHP (Fase 4, #18–#22)
- Gestor entitats al backend PHP femturisme (DEV-506, RF-13 CMS)
- RAG condicional al xat públic per `entity_id` (Fase 7, DEV-700–707)
- Indexació semàntica del catàleg MySQL ([preparacio-rag-cataleg.md](preparacio-rag-cataleg.md))
- Sign-off client staging (DEV-606) i producció (DEV-607)

---

## Referències

- [checklist-entrega.md](checklist-entrega.md) — DEV-500…507
- [postgre_schema.md](../postgre_schema.md) · [schema-agent-postgres.sql](../schema-agent-postgres.sql)
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9–10 (Fases 5–6)
- [tecnic.md](../client/tecnic.md) §6.12, §9.4–9.6, §14.4
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.7
- [preparacio-rag-cataleg.md](preparacio-rag-cataleg.md) — futur RAG catàleg
