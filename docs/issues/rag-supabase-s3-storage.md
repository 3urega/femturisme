## Objectiu

Migrar l'emmagatzematge de PDFs de **disc local** (`data/guides/`) a **Supabase Storage (API S3-compatible)**, al costat de la PostgreSQL ja desplegada al mateix projecte.

**Prerequisit ops:** bucket creat al dashboard Supabase Storage (recomanat: `guides`, privat) + claus S3 del projecte.

**Fora d'abast:** migració automàtica de PDFs ja existents a disc (script manual opcional); CDN públic dels PDFs.

---

## Context

Avui [`document_storage.py`](../../app/services/document_storage.py) escriu a `DOCUMENT_STORAGE_PATH/{doc_id}/original.pdf`. El pipeline (`indexing_pipeline.py`) llegeix des de ruta local. La decisió ops és Supabase S3:

| Paràmetre | Valor (projecte `upoczpgrybtbahivemal`) |
|-----------|----------------------------------------|
| Endpoint | `https://upoczpgrybtbahivemal.storage.supabase.co/storage/v1/s3` |
| Regió | `eu-central-1` |
| Bucket | `guides` (configurable via `S3_BUCKET`) |

Variables ja preparades a [`.env.example`](../../.env.example) i [`app/config.py`](../../app/config.py). **Implementació pendent.**

---

## Alcance

| In | Fuera |
|----|-------|
| Abstracció `StorageBackend` (`local` \| `s3`) | Multicloud abstract factory |
| Backend S3 via `boto3` (path-style, Supabase endpoint) | Supabase SDK REST alternatiu |
| Refactor `document_storage.py` | Canvi de model embedding |
| Upload/delete/read usats per admin + pipeline | UI canvis |
| `storage_path` lògic `{doc_id}/original.pdf` o prefix `s3://` documentat | Migració batch producció |
| Tests unitaris backend local + integració S3 opt-in | |

---

## Decisions tècniques

1. **`STORAGE_BACKEND=local|s3`** — default `local` per tests/CI sense credencials.
2. **Clau d'objecte S3:** `{doc_id}/original.pdf` dins bucket `S3_BUCKET`.
3. **Pipeline:** descarregar a tempfile o llegir bytes via `get_object` abans de PyMuPDF (no assumir path local quan `s3`).
4. **`guide_documents.storage_path`:** guardar clau lògica estable (`guides/{doc_id}/original.pdf` o `s3://{bucket}/{doc_id}/original.pdf`) — documentar contracte.
5. **boto3** a `requirements.txt`; config: `endpoint_url`, `region_name`, `aws_access_key_id`, `aws_secret_access_key`, `addressing_style=path`.

---

## Slices verticals

| Slice | Entrega |
|-------|---------|
| **VS1** | `StorageBackend` + refactor `LocalStorageBackend`; `config.py` wiring |
| **VS2** | `S3StorageBackend` (put/get/delete/exists) Supabase-compatible |
| **VS3** | `admin.py` upload/delete + `indexing_pipeline` read via backend |
| **VS4** | Tests + `docs/devs/desenvolupament-local.md` §storage + actualitzar `tecnic.md` §7.3 |

---

## Criteris d'acceptació

- [ ] `STORAGE_BACKEND=s3` + vars S3: upload API desa PDF al bucket Supabase
- [ ] Pipeline indexa PDF des de S3 (status `indexed`, chunks > 0)
- [ ] `DELETE /admin/api/documents/{id}` elimina objecte S3 + fila BD
- [ ] `STORAGE_BACKEND=local` (default) manté comportament actual; pytest CI sense S3
- [ ] Test integració opt-in (`S3_*` configurat) o mock boto3
- [ ] `requirements.txt` inclou `boto3`
- [ ] Documentació: crear bucket privat `guides`, generar claus S3, **mai** commitar secrets

---

## Fitxers principals

- `app/services/document_storage.py` — refactor + backends
- `app/services/storage_backends/` (nou) o mòduls col·locats
- `app/config.py` — ja té vars; usar-les
- `app/routes/admin.py`, `app/services/indexing_pipeline.py`
- `requirements.txt`
- `tests/unit/test_document_storage.py`, `tests/integration/rag/test_s3_storage.py` (opt-in)

---

## Verificació

```powershell
# .env local (NO commitar)
STORAGE_BACKEND=s3
S3_ENDPOINT=https://upoczpgrybtbahivemal.storage.supabase.co/storage/v1/s3
S3_REGION=eu-central-1
S3_BUCKET=guides
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...

python -m pytest tests/unit/test_document_storage.py -v
# Upload via admin API → comprovar objecte al dashboard Supabase Storage
```

---

## Referències

- [Supabase Storage S3 compatibility](https://supabase.com/docs/guides/storage/s3/compatibility)
- [auditoria-fase5-rag.md](../devs/auditoria-fase5-rag.md)
- [tecnic.md](../client/tecnic.md) §7.3
- Issue relacionada hardening: #34
