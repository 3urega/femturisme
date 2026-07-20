## Objetivo

Actualitzar el **system prompt** perquè el LLM passi `distance_km` i `category` correctes en consultes d'ofertes «a X km de Y» (p. ex. visites guiades prop de Calella).

## Contexto

- Tool amb `distance_km` ([#2](experiences-distance-km.md))
- Prompt actual distingeix agenda ≠ experiències però **no** menciona radi km
- [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py) — `_TOOL_GUIDE_CA['search_experiences']`

## Alcance

| In | Fuera |
|----|-------|
| Secció o ampliació guia `search_experiences`: `distance_km` + exemples | Heurística server-side obligatòria (opcional futur) |
| Exemple: «visites guiades a 50 km de Calella» → `destination`, `category`, `distance_km` | Radi a establishments/events |
| Distinció: radi km → `search_experiences`; agenda amb data → `search_events` | Llista tancada de categories |

## Criterios de aceptación

- [ ] Prompt documenta paràmetre `distance_km` i mapping «km de / a X km»
- [ ] Exemple concret visites guiades + municipi (Calella o genèric)
- [ ] `pytest tests/unit/test_prompts.py -v` actualitzat
- [ ] No confondre amb `search_destinations` («què veure a X» sense oferta)

## Capas / archivos principales

- `app/prompts/femturisme.py`
- `tests/unit/test_prompts.py`

## Issues relacionadas

- Prerequisit: `experiences-distance-km.md`
- Següent: `uat-experiences-radius.md`

## Verificación

```powershell
python -m pytest tests/unit/test_prompts.py -v
```

## Referencias

- [plan-experiences-radius.md](../devs/plan-experiences-radius.md)
- [funcional.md](../client/funcional.md) — consultes per proximitat
