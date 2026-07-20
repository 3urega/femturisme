## Objetivo

Quan l'usuari fa una consulta **temàtica o informativa** sobre un terme concret (festa, patrimoni, activitat, lloc…), l'agent ha de consultar el catàleg **automàticament** (articles + agenda) encara que el LLM no invoqui cap tool al primer torn.

**Patum és només el cas que va reportar el bug** — la implementació ha de ser **genèrica per keyword**, no una whitelist de festivals.

## Contexto

- El cercador web retorna tot tipus de contingut; l'agent depèn del routing LLM.
- Preguntes com «Què és X?», «Articles sobre castellers», «Mercat medieval a Vic» queden sovint **fora** de `is_agenda_search_query` i el model pot respondre sense dades.
- `search_articles` ja accepta `query`/`topic`; cal **forçar execució** quan hi ha termes cercables al missatge.
- Depèn de [#36](https://github.com/3urega/femturisme/issues/36) per la part agenda (`search_events` amb `query`).

## Alcance

| In | Fuera |
|----|-------|
| Extracció **genèrica** de keywords del missatge (stopwords ca/es/en, paraules meta «què», «quan», «recomana»…) | Whitelist hardcoded de festivals (Patum, Sant Jordi, …) |
| Si iteració 0 sense tool i hi ha ≥1 keyword significatiu → fan-out `search_articles` + `search_events` (post #36) | NLP extern / embeddings |
| Mòdul compartit `query_keywords.py` (o similar) reutilitzat per [#38](https://github.com/3urega/femturisme/issues/38) | Mode entitat / RAG |
| Injectar resultats combinats al prompt del segon torn LLM | Canvis PHP |
| Longitud mínima token (p.ex. ≥3 caràcters); excloure territoris sols si ja coberts per agenda force | Llista infinita mantinguda a mà |

## Criterios de aceptación

- [ ] Consulta genèrica «Articles sobre castellers a Barcelona» → crida a `search_articles` amb keyword extret (p.ex. `castellers`)
- [ ] Consulta informativa «Què és la Patum?» → crida a `search_articles` i/o `search_events` amb keyword `patum` (cas de prova, **no** `if "patum"`)
- [ ] Consulta temporal «Quan és la Fira medieval de Pals?» → crida a `search_events` amb `query` extret (post #36)
- [ ] Resposta final inclou enllaços femturisme.cat quan `total ≥ 1`
- [ ] No regressió a `uat_catalog_battery.py` (routing existent)
- [ ] Tests unitaris extractor + ≥3 casos API diversos (Patum + almenys 2 temes no-festival)

## Capas / archivos principales

- `app/services/query_keywords.py` (nou) — extracció compartida
- `app/services/agent_service.py` — `_handle_forced_keyword_search` paral·lel a agenda force
- `tests/unit/test_query_keywords.py`
- `tests/api/test_chat.py` — casos diversos (Patum, castellers, fira medieval…)

## Issues relacionadas

- [#36](https://github.com/3urega/femturisme/issues/36) events-keyword-query
- [#38](https://github.com/3urega/femturisme/issues/38) agent-zero-results-fallback
- [#39](https://github.com/3urega/femturisme/issues/39) prompt-theme-queries
- [#40](https://github.com/3urega/femturisme/issues/40) uat-catalog-recall-battery

## Verificación

```powershell
python -m pytest tests/unit/test_query_keywords.py tests/api/test_chat.py -v
python scripts/uat_recall_battery.py http://127.0.0.1:5010
```

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md)
- [agent_service.py](../../app/services/agent_service.py) — `build_forced_search_events_input`
