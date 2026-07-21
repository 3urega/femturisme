## Objetivo

En seguiments d'**allotjament** («si», «2 o 3 més», «no cal que siguin rurals»), l'agent ha de continuar només amb `search_establishments` i **no** reactivar el flux temàtic (`search_articles` + `search_events`) heretat d'un torn anterior (p.ex. Patum).

## Contexto

Conversa reportada: després de Patum, el torn «2 o 3 mes siusplau» va disparar **Cercant articles… Cercant events…** a més d'establiments.

Causes possibles:

1. **Historial LLM:** el model reutilitza el patró del primer torn informatiu.
2. **`query_keywords.py`:** missatges curts amb tokens com «siusplau» poden activar `build_forced_keyword_tool_calls` o fallback si `total=0`.
3. **Prompt:** falta regla «seguiment d'allotjament → només establishments».

## Alcance

| In | Fuera |
|----|-------|
| Regles al prompt: seguiments d'allotjament / menjar → no articles/events | Refactor complet de `AgentService` |
| Exclusió a `query_keywords.py` per missatges de seguiment (domini dormir/menjar, respostes curtes «si», «2 o 3 més») | Eliminar flux temàtic global (#37) |
| Tests unitaris `test_query_keywords.py` + `test_prompts.py` | UAT (issue #49) |

## Criterios de aceptación

- [ ] Prompt: després d'una cerca d'allotjament, seguiments («més opcions», «si», «no cal rural») → **només** `search_establishments` amb paràmetres coherents del context.
- [ ] `should_force_keyword_search()` retorna `False` per missatges de seguiment d'establiments (p.ex. «2 o 3 mes siusplau», «si» després de proposta d'allotjament) quan el domini ja és dormir/menjar.
- [ ] `build_keyword_fallback_calls` no afegeix articles/events en aquests seguiments.
- [ ] `pytest tests/unit/test_query_keywords.py tests/unit/test_prompts.py -q` passa.

## Capas / archivos principales

- [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py)
- [`app/services/query_keywords.py`](../../app/services/query_keywords.py)
- [`tests/unit/test_query_keywords.py`](../../tests/unit/test_query_keywords.py)
- [`tests/unit/test_prompts.py`](../../tests/unit/test_prompts.py)

## Issues relacionadas

- #45 — type genèric
- #46 — distance_km
- #49 — UAT

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md) — flux temàtic (#37–#40)
- [plan-establishments-proximity.md](../devs/plan-establishments-proximity.md)

## Verificación

```bash
pytest tests/unit/test_query_keywords.py tests/unit/test_prompts.py -q
```
