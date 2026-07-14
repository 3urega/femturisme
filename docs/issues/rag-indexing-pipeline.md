## Objetivo

Pipeline automàtic d'indexació: extracció de text PDF → chunks → embeddings → pgvector. Tanca **DEV-504**.

## Contexto

- Després de la pujada (`status=pending`), el document passa per `extracting` → `chunking` → `embedding` → `indexed` o `failed`.
- Model: `EMBEDDING_MODEL` (defecte `text-embedding-3-small`, 1536 dims).
- v1: job síncron en background thread o execució immediata post-upload; sense Redis/Celery obligatori.
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9 descriu el flux pas a pas.

## Alcance

| In | Fuera |
|----|-------|
| `EmbeddingService` — crida API OpenAI (batch chunks) | Reindexació catàleg MySQL |
| Extracció PDF (`pymupdf` o `pdfplumber`) | OCR de PDFs escanejats |
| Chunking 500–1000 tokens, overlap 10–15% | Celery/Redis (opcional futur) |
| Inserció `document_chunks` amb `embedding vector(1536)` | Cerca semàntica (issue següent) |
| `POST /admin/api/documents/{doc_id}/reindex` | Panell UI (issue `rag-admin-ui-uat.md`) |
| Actualització `guide_documents`: comptadors, `error_message`, `indexed_at` | |

## Criterios de aceptación

- [ ] PDF de prova indexat arriba a `status=indexed` amb `chunks_count > 0` i `embedded_chunks_count == chunks_count`
- [ ] PDF buit o corrupte → `status=failed` amb `error_message` informatiu
- [ ] Reindex esborra chunks antics del `doc_id` i incrementa `version`
- [ ] Logs estructurats: `doc_id`, pas, durada, chunks OK/KO
- [ ] Tests `tests/integration/rag/test_indexing_pipeline.py` (mock embedding API o fixture)
- [ ] Checklist **DEV-504** marcat

## Capas / archivos principales

- `app/services/embedding_service.py`
- `app/services/pdf_extractor.py`
- `app/services/chunking.py`
- `app/services/indexing_pipeline.py`
- `app/db/repositories/document_chunks.py`
- `requirements.txt` (pymupdf o pdfplumber si falta)

## Issues relacionadas

- `rag-documents-upload.md` (prerequisit)
- `rag-search-entity-knowledge.md` (següent)

## Verificación

```powershell
python -m pytest tests/integration/rag/test_indexing_pipeline.py -v
# Flux manual: upload PDF → esperar indexed → consultar BD
python -c "from app.services.indexing_pipeline import run; run('<doc_id>')"
```

## Referencias

- [postgre_schema.md](../postgre_schema.md) — `guide_document_status`, `document_chunks`
- [tecnic.md](../client/tecnic.md) §7 (pipeline)
- [plan-fase5-rag-base.md](../devs/plan-fase5-rag-base.md)
