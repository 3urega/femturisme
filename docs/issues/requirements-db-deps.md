## Objetivo

Ampliar `requirements.txt` amb dependències de base de dades i infra previstes a Fase 1–3, mantenint instal·lació local simple al Windows del developer.

## Contexto

- Checklist: **DEV-101**
- Avui `requirements.txt` té Flask, LLM providers, pytest i deps de scraping legacy.
- Cal preparar drivers MySQL i PostgreSQL abans d'implementar `app/db/connection.py`.
- No cal Docker local ([desenvolupament-local.md](../devs/desenvolupament-local.md)).

## Alcance

| In | Fuera |
|----|-------|
| Driver MySQL (`PyMySQL` recomanat — pur Python, Windows-friendly) | SQLAlchemy ORM (no necessari v1) |
| Driver PostgreSQL (`psycopg2-binary` o `psycopg[binary]`) | pgvector client especial (Fase 5) |
| Versions mínimes documentades | Eliminar scraping encara (legacy separat) |
| Verificar `pip install -r requirements.txt` en Windows | Embeddings / sentence-transformers (Fase 5) |

## Criterios de aceptación

- [ ] `requirements.txt` inclou `PyMySQL>=1.1` (o equivalent acordat)
- [ ] `requirements.txt` inclou client PostgreSQL (`psycopg2-binary>=2.9` o `psycopg[binary]`)
- [ ] `python -m pip install -r requirements.txt` OK en entorn net (Windows)
- [ ] `python -m pytest -v` segueix passant després d'instal·lar
- [ ] README o [desenvolupament-local.md](../devs/desenvolupament-local.md) menciona que les deps DB són per Fase 3+ (opcional, una línia)

## Capas / archivos principales

- `requirements.txt`

## Verificación

```powershell
python -m pip install -r requirements.txt
python -m pytest -v
```

## Issues relacionadas

- `config-env-example.md` — variables MYSQL_* / POSTGRES_*
- `db-layer-skeleton.md` — usa els drivers

## Referencias

- [tecnic.md §10](../client/tecnic.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-101
- [plan-fase1-base-local.md](../devs/plan-fase1-base-local.md)
