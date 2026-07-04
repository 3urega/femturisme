## Objetivo

Implementar `GET /health` per monitorització i desplegament (DEV-103), reportant estat del servei agent, MySQL i PostgreSQL segons [tecnic.md §9.3](../client/tecnic.md).

## Contexto

- Checklist: **DEV-103**
- Necessari per DEV-108 (staging Docker) i smoke tests post-deploy.
- Sense MySQL/PostgreSQL configurats, l'endpoint ha de respondre **200** amb estat `not_configured` o `skipped` — no 500.
- Depèn de: `db-layer-skeleton` (funcions ping).

## Alcance

| In | Fuera |
|----|-------|
| Ruta `GET /health` a `app/routes/api.py` (o blueprint dedicat) | Admin API |
| JSON amb `status`, `service`, `mysql`, `postgres` (objectes amb `ok` / `error` / `not_configured`) | Autenticació health |
| HTTP 200 quan el servei Flask respon (BD opcional) | HTTP 503 estricte si BD down (opcional: documentar decisió) |
| Test API a `tests/api/test_health.py` | Lògica de negoci |

## Criterios de aceptación

- [ ] `GET /health` retorna 200 i `Content-Type: application/json`
- [ ] Cos inclou almenys: `ok: true`, `service: "up"`, estat MySQL, estat PostgreSQL
- [ ] Sense `MYSQL_*`: mysql.status = `not_configured` (no error 500)
- [ ] Amb MySQL staging configurat: mysql.status = `ok` després de ping
- [ ] Test `tests/api/test_health.py` passa en CI/local sense MySQL
- [ ] Documentat a [testing.md](../devs/testing.md) com API-05 o equivalent
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/routes/api.py` (o `app/routes/health.py`)
- `app/db/connection.py` (ping)
- `tests/api/test_health.py`
- `docs/devs/testing.md` (mapatge test)

## Verificación

```powershell
python main.py
# Altra terminal:
curl.exe -s http://127.0.0.1:5010/health
python -m pytest tests/api/test_health.py -v
```

## Issues relacionadas

- `db-layer-skeleton.md`
- `config-env-example.md`

## Referencias

- [tecnic.md §9.3, §11.2](../client/tecnic.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-103, DEV-108
- [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md)
