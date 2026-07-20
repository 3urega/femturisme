## Objetivo

Si una tool de catàleg retorna **`total=0`** però el missatge de l'usuari conté termes cercables, reintentar automàticament amb **`search_articles`** i/o **`search_events`** abans que l'agent digui «no he trobat res».

Solució **genèrica per keyword** — comparteix extracció amb [#37](https://github.com/3urega/femturisme/issues/37); Patum només com a cas de prova.

## Contexto

- Escenari real: LLM crida `search_events(destination="Catalunya")` sense keyword → 0 resultats; articles amb `query=<term>` n'hi ha molts.
- [`execute_tool`](../../app/services/tools/__init__.py) ja té retry per territori ampli (`_skip_location_filter`); falta retry per **keyword**.
- Complementa [#37](https://github.com/3urega/femturisme/issues/37) (proactiu) amb fallback reactiu.

## Alcance

| In | Fuera |
|----|-------|
| Després de `tool_result` amb `total=0`, extreure tokens significatius via `query_keywords.py` (compartit amb #37) | Reescriure resposta LLM sencer |
| Reintent: `search_articles(query=…)` i `search_events(query=…)` si encara no s'han cridat | Més de 1 ronda extra (evitar loops) |
| Excloure stopwords i paraules genèriques («què», «és», «catalunya» sol) | Text-to-SQL |
| Whitelist de festivals | |
| Logging `meta.fallback_applied` | |

## Criterios de aceptación

- [ ] Simulació: LLM retorna `search_events` buit per consulta amb keyword «Patum» → fallback troba articles
- [ ] Simulació: consulta «castellers Barcelona» amb tool buida → fallback amb keyword `castellers`
- [ ] No duplica crides si la tool ja va ser `search_articles` amb el mateix query
- [ ] `MAX_TOOL_ITERATIONS` respectat
- [ ] Tests unitaris del extractor + integració API

## Capas / archivos principales

- `app/services/tools/__init__.py` o `app/services/agent_service.py`
- `app/services/query_keywords.py` (compartit amb #37)
- `tests/unit/test_catalog_fallback.py`

## Issues relacionadas

- [#37](https://github.com/3urega/femturisme/issues/37) agent-theme-routing
- [#36](https://github.com/3urega/femturisme/issues/36) events-keyword-query

## Verificación

```powershell
python -m pytest tests/unit/test_catalog_fallback.py -v
```

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md)
