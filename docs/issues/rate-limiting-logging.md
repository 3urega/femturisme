## Objetivo

Implementar **rate limiting** y **logging mínimo** en el servicio Flask según `tecnic.md` §12–13 (DEV-602), sin depender del portal PHP.

## Contexto

- Fase 4 (widget/proxy PHP) pospuesta; el chat de prueba Flask (`http://127.0.0.1:5010/`) es el entorno de validación.
- `tecnic.md` exige: límite de peticiones a `/api/chat` por IP/sesión y logs con `session_id`, idioma, latencia SQL y duración total del turno.
- Checklist: **DEV-602** abierto; prerequisito para staging/producción y para **DEV-605** (evidencia CA).

## Alcance

| In | Fuera |
|----|-------|
| Rate limit en `POST /api/chat` (por IP y/o `session_id`) | Rate limit en admin API (Fase 5) |
| Logging estructurado por request de chat | Dashboards / métricas externas (DEV-804) |
| Logging de consultas catálogo: tool, params, latencia SQL, row count | Logging RAG/pgvector (Fase 5) |
| Respuesta HTTP 429 cuando se supera el límite | Redis multi-instancia (P-04) |
| Tests unitarios del middleware/helper | Config nginx/apache (Fase 4) |

## Criterios de aceptación

- [ ] `POST /api/chat` devuelve **429** cuando se supera el límite configurado (IP o sesión)
- [ ] Cada turno de chat registra: `session_id`, duración total, idioma detectado, `agent_context.mode`, `entity_id` si aplica
- [ ] Cada tool de catálogo registra: nombre, parámetros relevantes (sin PII), latencia SQL, `total`/`row count`
- [ ] Errores registran `session_id` y mensaje/código sin exponer stack al cliente
- [ ] Límites configurables vía `.env` / `app/config.py` (valores por defecto razonables para dev)
- [ ] `pytest -q` verde; smoke manual: varias peticiones rápidas → 429

## Capas / archivos principales

- `app/config.py` — `AGENT_RATE_LIMIT_*`, flags de logging
- `app/routes/api.py` — aplicar rate limit al blueprint chat
- `app/services/agent_service.py` — log fin de turno (duración, idioma)
- `app/services/tools/__init__.py` o repositories — latencia SQL por consulta
- `tests/unit/test_rate_limit.py` (nuevo)
- `tests/unit/test_request_logging.py` (nuevo, opcional)
- `.env.example` — documentar variables nuevas

## Issues relacionadas

- `uat-conversation-context.md`
- `ca-matrix-verification.md`

## Verificación

```powershell
python -m pytest tests/unit/test_rate_limit.py -v
python -m pytest -q
# Smoke: 20 POST /api/chat rápidos → último 429
```

## Referencias

- [tecnic.md](../client/tecnic.md) §12, §13.1, T-PY-07
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-602
