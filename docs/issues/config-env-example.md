## Objetivo

Completar `app/config.py` i `.env.example` amb totes les variables d'entorn definides a [tecnic.md §10](../client/tecnic.md), per preparar connexions MySQL, PostgreSQL i embeddings sense dependre encara del client.

## Contexto

- Checklist: **DEV-102**, **DEV-109**
- Avui `config.py` només té variables LLM i `MAX_TOOL_ITERATIONS`.
- El client encara no ha aportat MySQL staging; les variables han de llegir-se correctament i tenir valors per defecte segurs.
- Desenvolupament local: [desenvolupament-local.md](../devs/desenvolupament-local.md) — LLM real al `.env`, sense Docker.

## Alcance

| In | Fuera |
|----|-------|
| Variables `MYSQL_*`, `POSTGRES_*`, timeouts, `LOG_LEVEL`, `EMBEDDING_MODEL` a `Config` | Implementar pools de connexió (issue db-layer-skeleton) |
| Prefix `AGENT_` + fallback sense prefix (patró actual `_env`) | Secrets reals al repo |
| `.env.example` documentat i alineat amb tecnic §10.2–10.3 | Admin API token / RAG pipeline |
| Actualitzar [desenvolupament-local.md](../devs/desenvolupament-local.md) §7 si cal | PostgreSQL funcional |

## Criterios de aceptación

- [ ] `app/config.py` exposa `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_CONNECT_TIMEOUT`
- [ ] `app/config.py` exposa `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE`, `POSTGRES_CONNECT_TIMEOUT`
- [ ] Variables opcionals: `LOG_LEVEL`, `EMBEDDING_MODEL`, `DOCUMENT_STORAGE_PATH` (valors per defecte raonables)
- [ ] `.env.example` complet sense secrets; comentaris per secció (Agent, MySQL, PostgreSQL, Embeddings)
- [ ] Llegir amb `AGENT_MYSQL_HOST` o `MYSQL_HOST` (mateix patró que LLM)
- [ ] `create_app('testing')` segueix funcionant; `python -m pytest -v` passa

## Capas / archivos principales

- `app/config.py`
- `.env.example`
- `docs/devs/desenvolupament-local.md` (referència variables, si cal)

## Verificación

```powershell
python -c "from app import create_app; c=create_app('testing').config; assert hasattr(c,'MYSQL_HOST')"
python -m pytest -v
```

## Issues relacionadas

- `requirements-db-deps.md` — drivers pip
- `db-layer-skeleton.md` — usa aquestes variables
- `health-endpoint.md` — llegeix estat via connection

## Referencias

- [tecnic.md §10](../client/tecnic.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-102, DEV-109
- [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md)
