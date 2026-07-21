## Objetivo

Evitar que l'agent filtri `type=cases-rurals` quan l'usuari demana **allotjament genèric** («on dormir», «allotjament a prop», «2 o 3 més») sense mencionar casa rural o turisme rural.

## Contexto

Conversa reportada: després de «Què en saps de la Patum?» i «allotjament a prop de Berga», el seguiment «2 o 3 mes siusplau» va acabar cercant **només cases rurals** i dient «no hi ha més cases rurals a Berga».

Causa principal: el prompt destaca `type=cases-rurals` a [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py) §Establiments sense aclarir que **només** s'aplica quan l'usuari ho demana explícitament. Berga/Berguedà accentua el sesgo del LLM cap al turisme rural.

Relacionat amb batch radi experiències ([#41](https://github.com/3urega/femturisme/issues/41)–[#44](https://github.com/3urega/femturisme/issues/44)): `distance_km` encara no existeix a establishments ([#46](https://github.com/3urega/femturisme/issues/46)).

## Alcance

| In | Fuera |
|----|-------|
| Regles al system prompt (`femturisme.py`) i `_TOOL_GUIDE_CA['search_establishments']` | Implementar `distance_km` (issue #46) |
| Exemple negatiu: «2 o 3 més» → **sense** `type` | Canvis al repository MySQL |
| Tests unitaris `tests/unit/test_prompts.py` | UAT script (issue #49) |

## Criterios de aceptación

- [ ] El prompt indica: allotjament genèric → `search_establishments` amb `destination` (i `distance_km` quan existeixi) **sense** `type`, llevat que l'usuari digui casa rural / camping / hotel / etc.
- [ ] Exemple explícit al prompt: «2 o 3 allotjaments més a Berga» → repetir cerca **sense** `type=cases-rurals`.
- [ ] `_TOOL_GUIDE_CA` alineat amb la mateixa regla.
- [ ] `pytest tests/unit/test_prompts.py -q` passa.

## Capas / archivos principales

- [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py)
- [`tests/unit/test_prompts.py`](../../tests/unit/test_prompts.py)

## Issues relacionadas

- #46 — `distance_km` a establishments
- #48 — seguiments sense articles/events
- #49 — UAT conversa Patum + Berga

## Referencias

- [dominio-femturisme-ca.md §5](../../client/dominio-femturisme-ca.md)
- [plan-establishments-proximity.md](../devs/plan-establishments-proximity.md)

## Verificación

```bash
pytest tests/unit/test_prompts.py -q
```
