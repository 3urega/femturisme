## Objetivo

Permetre pujar PDFs de guies, registrar-los a `guide_documents` i desar l'original a disc. Tanca **DEV-502** i **DEV-503**.

## Contexto

- Operadors interns pugen PDFs via API admin (panell Flask ve després).
- Emmagatzematge: `data/guides/{doc_id}/original.pdf` (`DOCUMENT_STORAGE_PATH`).
- Estat inicial: `pending` — el pipeline d'indexació és la issue següent.
- Contracte: [tecnic.md](../client/tecnic.md) §9.5–9.6.

## Alcance

| In | Fuera |
|----|-------|
| `POST /admin/api/documents/upload` (multipart: file, entity_id, title, category) | Pipeline extract/embed (issue `rag-indexing-pipeline.md`) |
| `GET /admin/api/documents` (filtre `?entity_id=`) | `POST .../reindex`, `smoke-test` (issues posteriors) |
| `GET /admin/api/documents/{doc_id}` | CLI `ingest_pdf.py` (opcional post-MVP) |
| `DELETE /admin/api/documents/{doc_id}` — esborra fila BD + fitxer disc | Validació antivirus / límit mida producció |
| `DocumentsRepository` CRUD sense vectors encara | DEV-506 PHP |

## Criterios de aceptación

- [ ] Pujada PDF crea `doc_id`, fila `guide_documents` amb `status=pending` i fitxer a `data/guides/{doc_id}/original.pdf`
- [ ] Llistat i detall retornen comptadors (`pages_count`, `chunks_count`, etc.) amb zeros inicials
- [ ] DELETE elimina registre i directori del document
- [ ] Error clar si `entity_id` no existeix o fitxer no és PDF
- [ ] Tests `tests/api/test_admin_documents.py` (upload mock o PDF petit de fixture)
- [ ] Checklist **DEV-502** i **DEV-503** marcats

## Capas / archivos principales

- `app/db/repositories/documents.py`
- `app/routes/admin.py` (ampliar)
- `app/services/document_storage.py`
- `tests/api/test_admin_documents.py`
- `tests/fixtures/sample-guide.pdf` (mínim, 1 pàgina)

## Issues relacionadas

- `rag-entities-api.md` (prerequisit)
- `rag-indexing-pipeline.md` (següent)

## Verificación

```powershell
python -m pytest tests/api/test_admin_documents.py -v
# Després de crear entitat de prova:
curl -s -F "file=@tests/fixtures/sample-guide.pdf" -F "entity_id=<uuid>" -F "title=Guia prova" http://127.0.0.1:5010/admin/api/documents/upload
```

## Referencias

- [tecnic.md](../client/tecnic.md) §9.5–9.6
- [postgre_schema.md](../postgre_schema.md) — `guide_documents`
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9
