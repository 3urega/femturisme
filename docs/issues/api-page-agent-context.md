## Objetivo

Implementar suport a **`page_context`** i **`agent_context`** al `POST /api/chat`, amb mode `femturisme` per defecte, i injectar el context al bucle de l'agent.

## Contexto

- Contracte API: [tecnic.md](../client/tecnic.md) §4.9, §8.x (camps opcionals al body).
- `app/routes/api.py` avui només accepta `message` i `session_id`.
- `AgentService.run()` no rep context; cal ampliar signatura i prompt (sense canviar tools Fase 1).
- Mode entitat (`mode: entitat`) es valida però **no** s'activa RAG públic en aquesta issue.

## Alcance

| In | Fuera |
|----|-------|
| Parsejar `page_context` (object) i `agent_context` (mode, entity_id) al body | Filtratge tools per mode entitat (Fase 7) |
| Default `agent_context.mode = femturisme`, `entity_id = null` | Implementació PHP que construeix page_context |
| Incloure context al system prompt o missatge sistema del torn | RAG condicional |
| Tests API/unit per camps nous | Widget JS (issue widget-context-reset) |

## Criterios de aceptación

- [ ] `POST /api/chat` accepta `page_context` i `agent_context` opcionals sense trencar clients existents
- [ ] Sense `agent_context`: mode femturisme implícit
- [ ] Amb `page_context.section` / `ubicacio` / `municipality`: el prompt o context del torn ho reflecteix
- [ ] `mode: entitat` sense `entity_id` → 400 amb missatge clar
- [ ] Test API nou o ampliació `test_api_03` verifica body amb context
- [ ] `pytest -v` verd

## Capas / archivos principales

- `app/routes/api.py`
- `app/services/agent_service.py`
- `app/prompts/femturisme.py` (o helper de context)
- `tests/api/test_chat.py`

## Issues relacionadas

- `widget-globus-assets.md` (paral·lel)
- `widget-context-reset.md` (consumidor widget)

## Verificación

```powershell
python -m pytest tests/api/test_chat.py -v
python -m pytest -v
```

## Referencias

- [tecnic.md](../client/tecnic.md) §4.9, §5.1
- [funcional.md](../client/funcional.md) — RF-14 modes
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-402, DEV-403
