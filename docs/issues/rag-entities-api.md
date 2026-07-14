## Objetivo

Implementar CRUD d'entitats documentals via API admin Flask. Tanca **DEV-501**.

## Contexto

- Cada entitat (ajuntament, museu, club…) és l'àmbit de la base de coneixement RAG.
- Contracte API: [tecnic.md](../client/tecnic.md) §9.4 (`/admin/api/entities`).
- Depèn de schema PostgreSQL (issue `rag-postgres-schema.md`).

## Alcance

| In | Fuera |
|----|-------|
| `EntitiesRepository` (create, list, get, update, delete) | UI web (issue `rag-admin-ui-uat.md`) |
| Blueprint Flask `app/routes/admin.py` amb rutas §9.4 | Autenticació producció (VPN/IP); v1: token/config mínim |
| Validació `entity_type` ENUM, `slug` únic | Integració CMS PHP (DEV-506) |
| Tests API o smoke curl documentats | `entity_id` a MySQL (DEV-700) |

## Criterios de aceptación

- [ ] `POST /admin/api/entities` crea entitat i retorna `entity_id` UUID
- [ ] `GET /admin/api/entities` llista entitats actives
- [ ] `GET/PUT/DELETE /admin/api/entities/{entity_id}` funcionen; DELETE fa CASCADE a documents (encara buits)
- [ ] Respostes JSON segons tecnic §9.4
- [ ] ≥3 tests a `tests/api/test_admin_entities.py`
- [ ] Checklist **DEV-501** marcat

## Capas / archivos principales

- `app/db/repositories/entities.py`
- `app/routes/admin.py`
- `tests/api/test_admin_entities.py`
- `app/__init__.py` (registrar blueprint)

## Issues relacionadas

- `rag-postgres-schema.md` (prerequisit)
- `rag-documents-upload.md` (següent)

## Verificación

```powershell
python -m pytest tests/api/test_admin_entities.py -v
# Smoke manual (amb token si s'activa):
curl -s -X POST http://127.0.0.1:5010/admin/api/entities -H "Content-Type: application/json" -d "{\"name\":\"Museu prova\",\"entity_type\":\"museu\"}"
```

## Referencias

- [tecnic.md](../client/tecnic.md) §9.4
- [postgre_schema.md](../postgre_schema.md) — taula `entities`
- [plan-fase5-rag-base.md](../devs/plan-fase5-rag-base.md)
