# Runbook — Admin RAG (guies PDF)

Operacions i resolució d'incidències per al batch Fase 5 (DEV-500…507, issue #34).

---

## Estats del pipeline

| Status | Significat | Acció |
|--------|------------|-------|
| `pending` | Registre creat, indexació encara no iniciada | Esperar o cridar reindex |
| `extracting` | Llegint text del PDF | Normal durant ingest |
| `chunking` | Generant fragments | Normal durant ingest |
| `embedding` | Creant vectors | Normal durant ingest |
| `indexed` | Completat OK | Cerca disponible |
| `failed` | Error en algun pas | Veure `error_message`, corregir i reindexar |

---

## Flux típic d'operació

1. Crear entitat (`POST /admin/api/entities`) o triar-ne una existent.
2. Pujar PDF (`POST /admin/api/documents/upload` o panell `/admin/guides/upload`).
3. Esperar status `indexed` al detall (`GET /admin/api/documents/{doc_id}`).
4. Provar cerca (`POST /admin/api/documents/{doc_id}/smoke-test` o CLI `--verify`).

---

## Autenticació admin

Quan `ADMIN_API_TOKEN` està configurat al `.env`:

- **API JSON:** header `Authorization: Bearer <token>`.
- **Panell HTML (`/admin/guides*`):** cookie `admin_api_token` (Path `/admin`, SameSite=Strict), sincronitzada des del camp token del panell.

Si el token és buit (dev/test), l'API i el panell queden oberts — **no usar en producció**.

### `ALLOWED_ADMIN_IPS` (defer)

Restricció per IP **no implementada** a v1. Mitigació recomanada: VPN, WAF o firewall davant del host agent. Variable documentada a `.env.example` per a una fase posterior.

---

## Document `failed`

1. Consultar `error_message` via API o panell detall.
2. Revisar logs del servei (`indexing step`, `failed`).
3. Corregir causa (PDF buit, fitxer absent a `data/guides/{doc_id}/`, API embedding, etc.).
4. Si cal, substituir `original.pdf` al directori del document.
5. `POST /admin/api/documents/{doc_id}/reindex` o botó **Reindexar** al panell.
6. Verificar amb smoke-test o:

```powershell
python scripts/ingest_pdf.py --verify DOC_ID --query "consulta prova"
```

---

## CLI `scripts/ingest_pdf.py`

Sense servidor HTTP (útil dev/staging):

```powershell
python scripts/ingest_pdf.py --list
python scripts/ingest_pdf.py --file guia.pdf --entity-id UUID --title "Títol" [--category patrimoni]
python scripts/ingest_pdf.py --verify DOC_ID --query "on aparcar" [--reindex]
```

Requereix `POSTGRES_*` al `.env` i, per indexar, clau OpenAI o embedder configurat.

---

## Esborrat d'entitats i documents

- **DELETE document:** esborra registre BD, chunks (CASCADE) i directori local `data/guides/{doc_id}/`.
- **DELETE entitat:** esborra tots els documents de l'entitat (CASCADE BD) i purga el storage local de cada PDF abans de l'entitat.

Upload a entitat amb `is_active=false` retorna **400**.

---

## Concurrencia (lock per `doc_id`)

`schedule_indexing` ignora una segona crida concurrent per al mateix `doc_id` (lock in-process). **Limitació:** no protegeix entre diversos workers Gunicorn; en desplegament multi-worker, evitar reindexacions paral·leles del mateix document o usar un sol worker per ingest.

---

## Verificació ràpida

```powershell
python -m pytest tests/api/test_admin_auth.py tests/integration/rag/test_rag_admin_lifecycle.py -v -m integration
python scripts/ingest_pdf.py --list
```

Veure [testing.md](testing.md) per la bateria completa §14.4.
