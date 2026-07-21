## Objetivo

Quan el **domini actiu del diàleg** és allotjament/menjar, injectar una instrucció per torn al system prompt (patró agenda) perquè confirmacions curtes («si», «30 km», «30 km des de Berga») cridin **només** `search_establishments` amb `distance_km` i destination del context — sense `search_experiences` ni flux temàtic.

## Contexto

- El prompt sol (#45–#49) no basta: missatges curts sense «allotjament» fallen B03 UAT [#49](https://github.com/3urega/femturisme/issues/49).
- `agent_service._with_system` ja injecta instruccions per agenda (`is_agenda_search_query`); cal paritat per domini establiments.
- `#48` va resoldre `query_keywords` per seguiments («2 o 3 més») **sense historial**; cal complement amb lectura lleugera de l'historial de sessió per detectar domini actiu.

## Alcance

| In | Fuera |
|----|-------|
| Nou mòdul o funcions a `app/services/` (p.ex. `domain_hints.py`): detectar domini allotjament actiu des de `history` + missatge actual | Historial persistent multi-servidor (fora d'abast) |
| `infer_establishment_domain_context(history, user_message)` → destination, distance_km suggerit, bool actiu | Forçar execució de tools sense LLM (excepte instrucció prompt) |
| Injectar bloc «Instrucció d'aquest torn» a `_with_system` quan actiu | Eliminar flux temàtic global |
| Skip `build_forced_keyword_tool_calls` / fallback quan domini allotjament actiu (reforç #48) | Canvis SQL |
| Tests unitaris `tests/unit/test_domain_hints.py` | UAT 4/4 (issue separada) |

## Criterios de aceptación

- [ ] Funció detecta domini allotjament actiu si: (a) torn anterior usuari menciona dormir/allotjament/menjar/prop de {destí}, (b) assistent va preguntar km després d'allotjament, o (c) `search_establishments` executat en torns recents.
- [ ] Missatges «30 km», «si», «si, 30 km», «30 km des de Berga» amb domini actiu → instrucció injectada exigeix `search_establishments` + `distance_km` + `destination` coherents.
- [ ] Amb domini actiu, `should_force_keyword_search` / `build_keyword_fallback_calls` retornen False (no articles/events).
- [ ] Sense domini actiu (consulta neta «Visitas guiades a 50 km de Calella»), comportament experiències (#44) **no** regressa.
- [ ] `pytest tests/unit/test_domain_hints.py tests/unit/test_query_keywords.py -q` passa.

## Capas / archivos principales

- [`app/services/domain_hints.py`](../../app/services/domain_hints.py) (nou)
- [`app/services/agent_service.py`](../../app/services/agent_service.py) — `_with_system`, opcionalment iteració 0
- [`app/services/query_keywords.py`](../../app/services/query_keywords.py) — integració skip si domini actiu
- [`tests/unit/test_domain_hints.py`](../../tests/unit/test_domain_hints.py) (nou)

## Issues relacionadas

- `prompt-proximity-establishments-vs-experiences` — complement prompt (implementar abans o en paral·lel)
- `uat-establishments-proximity-regression` — validació 4/4

## Referencias

- [plan-establishments-routing-debt.md](../devs/plan-establishments-routing-debt.md)
- [agente.md](../agente.md)
- [patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md)

## Verificación

```bash
python -m pytest tests/unit/test_domain_hints.py tests/unit/test_query_keywords.py -q
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```
