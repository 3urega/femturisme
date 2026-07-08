## Objetivo

Alinear el system prompt de l'agent amb els **6 dominis** de catàleg, distincions de negoci i idiomes (DEV-310).

## Contexto

- Checklist: **DEV-310**
- Avui `SYSTEM_PROMPT` a [agent_service.py](../../app/services/agent_service.py) menciona 4 tools legacy i scraping implícit.
- Després del registry cleanup (issue anterior), el prompt ha de reflectir tools reals registrades.
- Fase 1: mode femturisme sense RAG públic.

## Alcance

| In | Fuera |
|----|-------|
| Extreure prompt a `app/prompts/femturisme.py` (o mòdul equivalent) | Mode entitat (Fase 2) |
| Descriure 6 dominis: establishments, articles, destinations, routes, events, experiences | RAG condicional per `entity_id` |
| Regla agenda ≠ experiències | Filtratge dinàmic de tools per mode |
| Idioma de resposta = idioma de la pregunta (ca/es/en) | Canvis a `llm_service.py` |
| | Tests unitaris prompt (issue final) |

## Criterios de aceptación

- [ ] Prompt no menciona scraping ni `search_accommodations`
- [ ] Prompt distingeix agenda (dates) vs experiències (promocionals)
- [ ] Prompt llista tools registrades a `ALL_TOOLS` (mínim les 3 MySQL + legacy pendents)
- [ ] Smoke manual: pregunta al xat en català → resposta coherent amb tools disponibles
- [ ] `python -m pytest -v` passa (suite existent)

## Capas / archivos principales

- `app/prompts/femturisme.py` (nou)
- `app/services/agent_service.py`

## Verificación

```powershell
python -m pytest -v
python main.py
# POST /api/chat amb pregunta d'agenda o establiments
```

## Issues relacionadas

- `tool-registry-legacy-cleanup.md`

## Referencias

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md)
- [funcional.md](../client/funcional.md) §7
- [agente.md](../agente.md)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-310
