# Auditoria Fase 5 RAG (DEV-500–507)

**Data:** 2026-07-20  
**Abast:** batch tancat (#27–#33, issues DEV-500…507 Python)  
**Issue derivada:** [#34](https://github.com/3urega/femturisme/issues/34) hardening · [#35](https://github.com/3urega/femturisme/issues/35) Supabase S3 storage

---

## Resum executiu

El **nucli RAG Python està implementat i verificat** per al MVP dev/staging: schema pgvector, pipeline extract→chunk→embed→indexed, API admin, tool `search_entity_knowledge` (fora del LLM públic), UI Flask mínima i bateria UAT.

No hi ha senyals d’implementació «a mitges» al pipeline (#33). Els riscos accionables es concentren en **seguretat admin**, **higiene de disc**, **CLI documentada però absent**, **indexació en thread daemon** i **forats de tests** respecte `tecnic.md` §14.4.

**DEV-506** (gestor PHP) roman obert i és **fora** d’aquest batch.

---

## Confirmat OK

| Àrea | Evidència |
|------|-----------|
| Schema PostgreSQL | `docs/schema-agent-postgres.sql`, `tests/integration/postgres/test_schema.py` |
| Repositories | `entities.py`, `documents.py` (+ `search`), `document_chunks.py` |
| Pipeline | `indexing_pipeline.py`, `pdf_extractor.py`, `chunking.py`, `embedding_service.py` |
| Storage PDF | `document_storage.py` → `data/guides/{doc_id}/original.pdf` |
| Admin API | `app/routes/admin.py` — CRUD entitats/documents, reindex, smoke-test |
| Tool RAG | `entity_knowledge.py` a `ALL_TOOLS`, no a `CATALOG_TOOLS` |
| Admin UI | `admin_ui.py` + 3 pantalles `/admin/guides*` |
| Tests integració | `test_indexing_pipeline`, `test_search_entity_knowledge`, `test_rag_admin_lifecycle`, `test_admin_*` |
| UAT script | `scripts/uat_rag_battery.py` (6 casos, umbral 80%) |

---

## Gaps per severitat

### Alta

1. **PDFs orfes en esborrar entitat** — `DELETE /admin/api/entities/{id}` fa CASCADE a BD però **no** crida `delete_document_dir()` per cada `doc_id`. Només `DELETE document` neteja disc (`admin.py` 208–211 vs 94–103).

2. **UI admin HTML sense auth** — `admin_ui.py` no aplica `require_admin_token`; `/admin/guides*` accessible si la URL és reachable. L’API pot exigir Bearer però el token es demana manualment al JS.

3. **`ADMIN_API_TOKEN` buit = API oberta** — `admin_auth.py`: bypass total en dev; risc si es desplega a prod sense token.

4. **UAT battery no és CI-friendly** — `uat_rag_battery.py` requereix servidor viu + OpenAI real per indexar via upload; DEV-507 marcat amb pytest + script manual.

### Mitjana

5. **CLI `scripts/ingest_pdf.py` absent** — documentat a `plan-integracion-ca.md` §9.6 però no existeix al repo.

6. **`ALLOWED_ADMIN_IPS` no implementat** — deute documentat a `.env.example` / `tecnic.md` §10.3.

7. **Indexació en thread sense lock** — `schedule_indexing` pot llançar pipelines concurrents sobre el mateix `doc_id` (doble reindex).

8. **Jobs perduts en reiniciar Flask** — threads daemon; upload pot quedar `pending`/`embedding` forever.

9. **Entitat inactiva** — upload accepta entitat existent encara que `is_active=false`; search la rebutja. Comportament inconsistent.

10. **Cap test HTTP de `POST .../reindex`** — reindex provat via `run()` directe, no endpoint 202.

11. **`plan-integracion-ca.md` §9 desactualitzat** — rutes `/admin/api/guides/*`, `municipality`, tool legacy.

### Baixa

12. Dimensió embedding hardcoded 1536.  
13. `document_chunks.entity_id` sense FK (disseny intencional denormalitzat).  
14. UI admin sense nom d’entitat (només UUID).  
15. Test schema no verifica índex HNSW.

---

## Tests §14.4 pendents

| Requisit | Estat |
|----------|--------|
| PUT entity (update) | Sense test |
| Upload API → `indexed` (poll) | Només `run()` directe |
| `failed` → reindex → `indexed` | Absent |
| Auth 401 amb token configurat | Absent |
| Filtre `category` a search | Sense test dedicat |

---

## Recomanació

Un sol issue de **hardening post-Fase 5** (Python/ops), sense barrejar DEV-506 PHP:

Veure [rag-fase5-hardening.md](../issues/rag-fase5-hardening.md).
