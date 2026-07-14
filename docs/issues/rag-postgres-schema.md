## Objetivo

Aplicar el schema PostgreSQL de l'agent (entitats + documents + chunks + pgvector) en entorn local i deixar un script de migració repetible. Tanca **DEV-500**.

## Contexto

- DDL documentat a [schema-agent-postgres.sql](../schema-agent-postgres.sql) i [postgre_schema.md](../postgre_schema.md).
- `app/db/connection.py` ja té `get_postgres_connection()` i `ping_postgres()`; falta crear les taules.
- Prerequisit de tot el batch RAG (DEV-501…507).
- Staging remot (DEV-023) pot reutilitzar el mateix script quan hi hagi accés.

## Alcance

| In | Fuera |
|----|-------|
| Script `scripts/apply_postgres_schema.py` (idempotent: `IF NOT EXISTS`) | Canvis de schema no documentats |
| Verificar extensió `vector` (pgvector) | Qdrant o altres vector stores |
| Test d'integració: taules `entities`, `guide_documents`, `document_chunks` existeixen | Dades de prova (issue següent) |
| Actualitzar [desenvolupament-local.md](../devs/desenvolupament-local.md) si cal pas PostgreSQL | DEV-506 PHP |

## Criterios de aceptación

- [ ] `python scripts/apply_postgres_schema.py` aplica DDL sense errors contra PostgreSQL local
- [ ] `GET /health` retorna `postgres.status: ok` amb `POSTGRES_HOST` configurat
- [ ] Test `tests/integration/postgres/test_schema.py` passa (taules + tipus ENUM + extensió vector)
- [ ] Checklist **DEV-500** marcat; progrés checklist actualitzat

## Capas / archivos principales

- `docs/schema-agent-postgres.sql`
- `scripts/apply_postgres_schema.py`
- `tests/integration/postgres/test_schema.py`
- `app/db/connection.py` (reutilitzar)
- `docs/devs/checklist-entrega.md` — DEV-500

## Issues relacionadas

- `rag-entities-api.md` (següent)

## Verificación

```powershell
python scripts/apply_postgres_schema.py
python -m pytest tests/integration/postgres/test_schema.py -v
curl -s http://127.0.0.1:5010/health
```

## Referencias

- [postgre_schema.md](../postgre_schema.md)
- [schema-agent-postgres.sql](../schema-agent-postgres.sql)
- [plan-fase5-rag-base.md](../devs/plan-fase5-rag-base.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-500
